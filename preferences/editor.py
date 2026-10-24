#!/usr/bin/env python3
"""Apply only the editor defaults listed in editor.json, keeping local backups."""

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


CODEX_KEY = "open-in-target-preferences"


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

    def read_editor(self):
        result = self.request("config/read", {"includeLayers": False})
        return result["config"].get("desktop", {}).get(CODEX_KEY)

    def write_editor(self, value):
        # Replace this one preference, including old per-project editor overrides.
        self.request("config/value/write", {
            "keyPath": "desktop." + CODEX_KEY,
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
    for command in ("xcrun", "codex", "git"):
        if shutil.which(command) is None:
            raise RuntimeError(f"Missing {command}; run provision/install.sh first")
    wanted = json.loads(Path(__file__).with_name("editor.json").read_text())
    app = next((p for p in (
        Path("/Applications/Zed.app"), Path.home() / "Applications/Zed.app",
    ) if p.exists()), None)
    if app is None:
        raise RuntimeError("Missing Zed; run provision/install.sh first")
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    if info["CFBundleIdentifier"] != wanted["bundle_id"]:
        raise RuntimeError("Zed's bundle identifier differs from editor.json")

    selectors = wanted["content_types"] + ["." + ext for ext in wanted["extensions"]]
    macos = MacFileHandlers(app)
    previous = macos.request("read", selectors)
    changed = [selector for selector, old in previous.items() if old != wanted["bundle_id"]]
    old_git = git_editor()
    desired_codex = {"global": wanted["codex_target"]}
    with CodexConfig() as codex:
        old_codex = codex.read_editor()
        codex_changed = old_codex != desired_codex
        git_changed = old_git != wanted["git_editor"]
        if args.check:
            print("drift    macOS file handlers: " + ", ".join(changed) if changed
                  else f"ok       macOS file handlers ({len(selectors)} types)")
            print("drift    Codex preferred editor" if codex_changed else "ok       Codex preferred editor")
            print("drift    Git editor" if git_changed else "ok       Git editor")
            return int(bool(changed or codex_changed or git_changed))
        if changed or codex_changed or git_changed:
            backup = save_backup({
                "macos_handlers": previous,
                "codex_editor": old_codex,
                "git_core_editor": old_git,
            })
            print(f"backup   {backup}", flush=True)
        if codex_changed:
            codex.write_editor(desired_codex)
        if git_changed:
            run("git", "config", "--global", "core.editor", wanted["git_editor"])
        if changed:
            print("note     choose Use Zed in macOS's file-default confirmations; waiting for completion", flush=True)
            macos.request("apply", changed)
        actual = macos.request("read", selectors)
        incorrect = [selector for selector in selectors if actual[selector] != wanted["bundle_id"]]
        if incorrect:
            raise RuntimeError("File handler verification failed: " + ", ".join(incorrect))
        if codex.read_editor() != desired_codex or git_editor() != wanted["git_editor"]:
            raise RuntimeError("Editor preference verification failed")
    print(f"ok       Zed is the macOS default for {len(selectors)} code/text file types")
    print("ok       Zed is Codex's preferred editor (per-project overrides cleared)")
    print("ok       Git uses zed --wait")
    if codex_changed:
        print("note     reopen Codex to load its new preferred editor")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"FAILED   {error}", file=sys.stderr)
        sys.exit(1)
