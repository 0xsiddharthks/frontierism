#!/usr/bin/env python3
"""Apply automatic macOS appearance and the defaults in editor.json, with backups."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time


AUTO_APPEARANCE_KEY = "AppleInterfaceStyleSwitchesAutomatically"
CLAUDE_EDITOR_KEY = "claude-code-preferred-editor"


class CodexConfig:
    """Use Codex's config API so edits preserve unrelated TOML and comments."""

    def __enter__(self):
        self.errors = tempfile.TemporaryFile()
        self.process = subprocess.Popen(
            ["codex", "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.errors,
            text=True,
        )
        self.replies = queue.Queue()
        self.next_id = 0
        self.reader = threading.Thread(target=self.collect, daemon=True)
        self.reader.start()
        try:
            self.request("initialize", {
                "clientInfo": {"name": "frontierism_preferences", "version": "1.0"},
            })
            self.send({"method": "initialized", "params": {}})
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def collect(self):
        for line in self.process.stdout:
            try:
                self.replies.put(json.loads(line))
            except ValueError:
                continue
        self.replies.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.next_id += 1
        request_id = self.next_id
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + 30
        while True:
            try:
                reply = self.replies.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty:
                raise RuntimeError(f"Codex {method} timed out") from None
            if reply is None:
                raise RuntimeError("Codex configuration server stopped unexpectedly")
            if reply.get("id") == request_id:
                if "error" in reply:
                    code = reply["error"].get("code")
                    message = reply["error"].get("message", "Configuration request failed")
                    raise RuntimeError(f"Codex {method} failed (error {code}): {message}")
                return reply["result"]

    def read_preferences(self, keys):
        result = self.request("config/read", {"includeLayers": False})
        selected = {}
        for key in keys:
            value = result["config"]
            for part in key.split("."):
                value = value.get(part) if isinstance(value, dict) else None
            selected[key] = value
        return selected

    def write_preferences(self, values):
        for key, value in values.items():
            # Replace only selected keys, including old per-project editor overrides.
            self.request("config/value/write", {
                "keyPath": key,
                "value": value,
                "mergeStrategy": "replace",
            })

    def __exit__(self, *_):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.reader.join(timeout=1)
        self.process.stdout.close()
        self.errors.close()


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


class MacFileHandlers:
    def __init__(self, application):
        self.application = str(application)
        source = Path(__file__).with_name("file-handlers.swift")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        directory = cache_root / "frontierism/preferences"
        directory.mkdir(parents=True, exist_ok=True)
        self.binary = directory / ("file-handlers-" + digest)
        if not self.binary.exists():
            subprocess.run(
                ["xcrun", "swiftc", "-O", str(source), "-o", str(self.binary)], check=True,
            )

    def request(self, mode, selectors):
        result = subprocess.run(
            [str(self.binary)],
            input=json.dumps({
                "mode": mode, "selectors": selectors, "application": self.application,
            }),
            capture_output=True, text=True, timeout=900 if mode == "apply" else 30,
        )
        if not result.stdout:
            raise RuntimeError("macOS file-handler helper failed: " + result.stderr.strip())
        response = json.loads(result.stdout)
        if response["errors"]:
            raise RuntimeError("macOS file defaults: " + json.dumps(response["errors"]))
        if result.returncode:
            raise RuntimeError("macOS file-handler helper failed")
        return response["handlers"]


def git_editor():
    result = subprocess.run(
        ["git", "config", "--global", "--get", "core.editor"],
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Cannot read Git's global editor preference")
    return result.stdout.strip() if result.returncode == 0 else None


def auto_appearance():
    result = subprocess.run(
        ["defaults", "read", "-g", AUTO_APPEARANCE_KEY],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip() in ("0", "1"):
        return result.stdout.strip() == "1"
    # defaults exits 1 when a fresh account has no value (or domain) yet.
    if result.returncode == 1:
        return None
    raise RuntimeError("Cannot read macOS's automatic appearance preference")


class ClaudePreferences:
    """Merge the editor choice without exporting accounts, MCP servers or other state."""

    def __init__(self):
        self.path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"

    def read(self):
        config = json.loads(self.path.read_text()) if self.path.exists() else {}
        if not isinstance(config, dict):
            raise ValueError("Claude's configuration is not a JSON object")
        preferences = config.get("preferences", {})
        if not isinstance(preferences, dict):
            raise ValueError("Claude's preferences are not a JSON object")
        epitaxy = preferences.get("epitaxyPrefs", {})
        if not isinstance(epitaxy, dict):
            raise ValueError("Claude's editor preferences are not a JSON object")
        return config, epitaxy.get(CLAUDE_EDITOR_KEY)

    def ensure_closed(self):
        result = subprocess.run(["pgrep", "-x", "Claude"], capture_output=True)
        if result.returncode == 0:
            raise RuntimeError("Quit Claude before applying its saved editor preference, then run the installer again")
        if result.returncode != 1:
            raise RuntimeError("Couldn't check whether Claude is running")

    def write_editor(self, value):
        self.ensure_closed()
        config, _ = self.read()
        config.setdefault("preferences", {}).setdefault("epitaxyPrefs", {})[CLAUDE_EDITOR_KEY] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".editor-", dir=self.path.parent)
        try:
            with os.fdopen(descriptor, "w") as output:
                json.dump(config, output, indent=2)
                output.write("\n")
            os.replace(temporary, self.path)
        finally:
            Path(temporary).unlink(missing_ok=True)


def save_backup(snapshot):
    state_root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    directory = state_root / "frontierism/preferences"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = directory / f"editor-before-{stamp}.json"
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(snapshot, output, indent=2)
        output.write("\n")
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="only report differences")
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise RuntimeError("These app defaults are for macOS")
    for command in ("xcrun", "codex", "git", "vim", "defaults", "pgrep"):
        if shutil.which(command) is None:
            raise RuntimeError(f"Missing {command}; run provision/install.sh first")
    wanted = json.loads(Path(__file__).with_name("editor.json").read_text())
    if not (Path(__file__).resolve().parents[1] / ".codex-root").is_file():
        raise RuntimeError("Missing repository .codex-root marker; restore it from Git")
    app = next((p for p in (
        Path("/Applications/Cursor.app"), Path.home() / "Applications/Cursor.app",
    ) if p.exists()), None)
    if app is None:
        raise RuntimeError("Missing Cursor; run provision/install.sh first")
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    if info["CFBundleIdentifier"] != wanted["bundle_id"]:
        raise RuntimeError("Cursor's bundle identifier differs from editor.json")

    selectors = wanted["content_types"] + ["." + ext for ext in wanted["extensions"]]
    macos = MacFileHandlers(app)
    previous = macos.request("read", selectors)
    changed = [selector for selector, old in previous.items() if old != wanted["bundle_id"]]
    old_git = git_editor()
    old_appearance = auto_appearance()
    appearance_changed = old_appearance is not True
    desired_codex = wanted["codex"]
    claude = ClaudePreferences()
    _, old_claude = claude.read()
    claude_changed = old_claude != wanted["claude_editor"]
    with CodexConfig() as codex:
        old_codex = codex.read_preferences(desired_codex)
        codex_changes = {key: value for key, value in desired_codex.items() if old_codex[key] != value}
        git_changed = old_git != wanted["git_editor"]
        if args.check:
            print("drift    macOS file handlers: " + ", ".join(changed) if changed
                  else f"ok       macOS file handlers ({len(selectors)} types)")
            for key in desired_codex:
                print(("drift    " if key in codex_changes else "ok       ") + "Codex " + key)
            print("drift    Claude preferred editor" if claude_changed else "ok       Claude preferred editor")
            print("drift    Git editor" if git_changed else "ok       Git editor")
            print("drift    macOS automatic appearance" if appearance_changed
                  else "ok       macOS automatic appearance")
            return int(bool(changed or codex_changes or claude_changed or git_changed or appearance_changed))
        if claude_changed:
            claude.ensure_closed()
        if changed or codex_changes or claude_changed or git_changed or appearance_changed:
            backup = save_backup({
                "macos_handlers": previous,
                "codex_preferences": old_codex,
                "claude_editor": old_claude,
                "git_core_editor": old_git,
                "macos_auto_appearance": old_appearance,
            })
            print(f"backup   {backup}", flush=True)
        codex.write_preferences(codex_changes)
        if claude_changed:
            claude.write_editor(wanted["claude_editor"])
        if git_changed:
            run("git", "config", "--global", "core.editor", wanted["git_editor"])
        if appearance_changed:
            run("defaults", "write", "-g", AUTO_APPEARANCE_KEY, "-bool", "true")
        if changed:
            print("note     choose Use Cursor in macOS's file-default confirmations; waiting for completion", flush=True)
            macos.request("apply", changed)
        actual = macos.request("read", selectors)
        incorrect = [selector for selector in selectors if actual[selector] != wanted["bundle_id"]]
        if incorrect:
            raise RuntimeError("File handler verification failed: " + ", ".join(incorrect))
        if codex.read_preferences(desired_codex) != desired_codex or git_editor() != wanted["git_editor"]:
            raise RuntimeError("Editor preference verification failed")
        if claude.read()[1] != wanted["claude_editor"]:
            raise RuntimeError("Claude editor preference verification failed")
        if auto_appearance() is not True:
            raise RuntimeError("Automatic appearance preference verification failed")
    print(f"ok       Cursor is the macOS default for {len(selectors)} code/text file types")
    print("ok       Cursor is Codex's preferred editor (per-project overrides cleared)")
    print("ok       Codex file links use Cursor; project roots use .codex-root with a 64 KiB instruction limit")
    print("ok       Cursor is Claude's preferred editor")
    print("note     GitHub Desktop selects Cursor on a new Mac as the only installed GUI code editor")
    print(f"ok       Git uses {wanted['git_editor']}")
    print("ok       macOS appearance switches automatically between light and dark")
    if codex_changes:
        print("note     reopen ChatGPT/Codex to load its new preferences")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"FAILED   {error}", file=sys.stderr)
        sys.exit(1)
