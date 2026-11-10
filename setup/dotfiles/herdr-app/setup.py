#!/usr/bin/env python3
"""Copy only personal Herdr files, then select the layout without launching the app."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
MODS = ("frontier-agents", "frontier-tabs", "frontier-workbench")
LAYOUT = "frontierism"
CREDENTIAL = re.compile(
    r"(^|[^A-Za-z0-9_-])(sk-(ant-)?[A-Za-z0-9_-]{20}|gh[pousr]_[A-Za-z0-9]{30}"
    r"|github_pat_[A-Za-z0-9_]{20}|xox[abprs]-[A-Za-z0-9-]{10}|(AKIA|ASIA)[0-9A-Z]{16}"
    r"|AIza[0-9A-Za-z_-]{35})|-----BEGIN [A-Z ]*PRIVATE KEY"
    r"|(api[_-]?key|secret|token|passw(or)?d)[a-z_]*[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9+/_.-]{16}",
    re.IGNORECASE | re.MULTILINE,
)


def managed_files():
    # No state, sockets, telemetry, generated docs/types or other people's mods.
    yield Path("settings.json")
    yield Path("keys.json")
    for folder in ("themes", "layouts"):
        yield from (p.relative_to(ROOT) for p in sorted((ROOT / folder).glob("*"))
                    if p.is_file() and p.suffix in (".json", ".svg"))
    for mod in MODS:
        for name in ("main.js", "mod.json"):
            yield Path("mods") / mod / name


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_json(path, data):
    write(path, (json.dumps(data, indent=2) + "\n").encode())


def backup(path):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    saved = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, saved)
    return saved


def sync(app_home, mode):
    failed = False
    for relative in managed_files():
        source, installed = ROOT / relative, app_home / relative
        if mode == "--pull":
            source, destination = installed, source
        else:
            destination = installed
        if not source.is_file():
            print(f"missing  {source}")
            failed = True
            continue
        data = source.read_bytes()
        # Validate before replacing a working file, in either direction.
        if relative.suffix == ".json":
            json.loads(data)
        if mode == "--pull" and CREDENTIAL.search(data.decode()):
            print(f"REFUSED  {source} looks like it holds a credential")
            failed = True
            continue
        if destination.is_file() and data == destination.read_bytes():
            print(f"ok       {installed}")
        elif mode == "--check":
            print(f"drift    {installed}. Run ./setup/dotfiles/herdr-app/setup.py --push")
            failed = True
        elif destination.exists() and mode not in ("--push", "--pull"):
            print(f"drift    {installed}; --pull keeps home's, --push keeps this repo's")
            failed = True
        else:
            saved = backup(destination) if destination.exists() and mode != "--pull" else None
            write(destination, data)
            verb = "pulled" if mode == "--pull" else "updated" if saved else "copied"
            print(f"{verb:8} {installed}" + (f" (backup: {saved})" if saved else ""))
    return not failed


def cli_path():
    found = shutil.which("herdr-app")
    candidate = found or str(Path.home() / ".local/bin/herdr-app")
    if not os.access(candidate, os.X_OK):
        raise RuntimeError("Herdr app is missing. Run ./setup/provision/install.sh first")
    return candidate


def command(cli, *args):
    return subprocess.run([cli, *args], capture_output=True, text=True, timeout=30)


def status(cli):
    result = command(cli, "status")
    if result.returncode:
        return None
    return json.loads(result.stdout)


def activate(cli, app_home, mode):
    current = status(cli)
    if current is None:
        path = app_home / "shared.json"
        state = json.loads(path.read_text()) if path.exists() else {}
        if mode == "--check":
            if state.get("layout") != LAYOUT:
                raise RuntimeError("Herdr's saved layout differs; run the dotfile installer")
        else:
            before = state.copy()
            state["layout"] = LAYOUT
            state.setdefault("frame.welcomed", "skipped")
            state.setdefault("agents.sort", "priority")
            if state != before:
                if path.exists():
                    backup(path)
                save_json(path, state)
        print("ok       Herdr layout saved; it loads when you open Herdr")
        return

    if mode != "--check":
        if current.get("layout") != LAYOUT:
            result = command(cli, "do", "layout.switch", "--name", LAYOUT)
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
        # The old config disabled onboarding. The personal agents mod remembers
        # that choice through setShared; close only this specific first-run screen.
        if "frame-welcome" in current.get("overlays", []):
            result = command(cli, "do", "overlay.close", "--id", "frame-welcome")
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
        # A save reloads asynchronously. Verify the result after the watcher runs.
        time.sleep(1)
        current = status(cli)
    if current is None:
        raise RuntimeError("Herdr closed during verification; run --check again")
    if current.get("errors"):
        raise RuntimeError("Herdr reported errors: " + json.dumps(current["errors"]))
    if current.get("layout") != LAYOUT:
        raise RuntimeError("Herdr is showing another layout; run the dotfile installer")
    print("ok       Herdr is showing frontierism; no file or mod errors")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    for flag in ("--check", "--push", "--pull"):
        group.add_argument(flag, dest="mode", action="store_const", const=flag)
    arguments = sys.argv[1:]
    mode = parser.parse_args([] if arguments == [""] else arguments).mode or ""
    app_home = Path(os.environ.get("HERDR_APP_HOME", str(Path.home() / ".config/herdr-app"))).expanduser()
    try:
        if not sync(app_home, mode):
            return 1
        if mode == "--pull":
            return 0
        cli = cli_path()
        # Checking a mod can generate editor metadata. Skip it in read-only mode;
        # a normal apply checks every mod, including while the window is closed.
        if mode != "--check":
            for mod in MODS:
                result = command(cli, "check", str(app_home / "mods" / mod))
                if result.returncode:
                    raise RuntimeError(result.stderr or result.stdout)
                print(f"ok       Herdr mod {mod}")
        activate(cli, app_home, mode)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"FAILED   Herdr: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
