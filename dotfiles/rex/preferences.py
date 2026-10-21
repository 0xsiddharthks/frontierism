#!/usr/bin/env python3
"""Sync only the Rex preferences explicitly named in preferences.json."""

import datetime
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    source = Path(__file__).with_name("preferences.json")
    wanted = json.loads(source.read_text())
    result = subprocess.run(
        ["defaults", "export", "com.superlogical.rex", "-"], capture_output=True
    )
    current = plistlib.loads(result.stdout) if result.returncode == 0 else {}
    if mode == "--pull":
        # Never export the rest of the plist: it contains machine and host state.
        for key in wanted:
            if key in current:
                wanted[key] = current[key]
        source.write_text(json.dumps(wanted, indent=2) + "\n")
        print("pulled   Rex preferences")
        return 0
    changed = {key: value for key, value in wanted.items() if current.get(key) != value}
    if not changed:
        print("ok       Rex preferences")
        return 0
    if mode == "--check":
        for key in changed:
            print(f"drift    Rex preference {key}")
        return 1
    drift = [key for key in changed if key in current] if mode != "--push" else []
    for key in drift:
        print(f"drift    Rex preference {key}: --pull keeps the app's, --push keeps this repo's")
        del changed[key]
    if not changed:
        return int(bool(drift))
    directory = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "rex"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = directory / f"preferences.bak-{stamp}.json"
    backup.write_text(json.dumps({key: current.get(key) for key in wanted}, indent=2) + "\n")
    for key, value in changed.items():
        kind = "-bool" if isinstance(value, bool) else "-float" if isinstance(value, (int, float)) else "-string"
        text = str(value).lower() if isinstance(value, bool) else str(value)
        subprocess.run(["defaults", "write", "com.superlogical.rex", key, kind, text], check=True)
    print(f"updated  Rex preferences (backup: {backup})")
    print("note     reopen Rex after changing its Mac preferences")
    return int(bool(drift))


if __name__ == "__main__":
    sys.exit(main())
