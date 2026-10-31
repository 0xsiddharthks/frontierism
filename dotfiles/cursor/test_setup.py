"""Exercise Cursor export and a new-Mac install without opening either editor."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("cursor_preferences", ROOT / "preferences.py")
preferences = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preferences)


def write_state(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)")
            connection.executemany("INSERT OR REPLACE INTO ItemTable VALUES (?, ?)",
                                   [(key, json.dumps(value)) for key, value in values.items()])


def read_state(path):
    with contextlib.closing(sqlite3.connect(path)) as connection:
        return {key: json.loads(value) for key, value in connection.execute("SELECT key, value FROM ItemTable")}


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.source = self.directory / "preferences.json"
        self.state = self.directory / "globalStorage/state.vscdb"
        self.wanted = {
            "applicationUser": {
                "cppEnabled": False,
                "composerState": {"defaultMode2": "agent"},
                "aiSettings": {"modelConfig": {"composer": {
                    "modelName": "default", "maxMode": True,
                    "selectedModels": [{"modelId": "default", "parameters": []}],
                }}},
            },
            "globalStorage": {"workbench.sideBar.size": 365},
        }
        self.source.write_text(json.dumps(self.wanted))
        self.running = patch.object(preferences, "cursor_running", return_value=False).start()
        self.addCleanup(patch.stopall)

    def sync(self, mode):
        with contextlib.redirect_stdout(io.StringIO()):
            return preferences.sync(self.source, self.state, mode)

    def test_new_profile_is_seeded_and_repeat_is_read_only(self):
        self.assertEqual(self.sync("--push"), 0)
        first = self.state.read_bytes()
        self.assertEqual(self.sync("--push"), 0)
        self.assertEqual(self.sync("--check"), 0)
        self.assertEqual(self.state.read_bytes(), first)
        self.assertEqual(list(self.state.parent.glob("*.bak-*")), [])

    def test_push_merges_and_backs_up_private_state(self):
        original = {
            preferences.APPLICATION_USER: {
                "cppEnabled": True,
                "cursorCreds": {"privateValue": "keep locally"},
                "aiSettings": {"accountOnly": "keep locally"},
            },
            "unrelatedState": {"privateValue": "keep locally"},
        }
        write_state(self.state, original)
        self.assertEqual(self.sync("--push"), 0)
        current = read_state(self.state)
        app = current[preferences.APPLICATION_USER]
        self.assertFalse(app["cppEnabled"])
        self.assertEqual(app["cursorCreds"], original[preferences.APPLICATION_USER]["cursorCreds"])
        self.assertEqual(app["aiSettings"]["accountOnly"], "keep locally")
        self.assertEqual(current["unrelatedState"], original["unrelatedState"])
        backups = list(self.state.parent.glob("*.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(read_state(backups[0]), original)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_plain_run_keeps_existing_values_and_adds_missing_preferences(self):
        write_state(self.state, {preferences.APPLICATION_USER: {"cppEnabled": True}})
        self.assertEqual(self.sync(""), 1)
        app = read_state(self.state)[preferences.APPLICATION_USER]
        self.assertTrue(app["cppEnabled"])
        self.assertEqual(app["composerState"]["defaultMode2"], "agent")

    def test_check_detects_drift_without_writes(self):
        self.assertEqual(self.sync("--check"), 1)
        self.assertFalse(self.state.exists())
        write_state(self.state, {preferences.APPLICATION_USER: {"cppEnabled": True}})
        before = self.state.read_bytes()
        self.assertEqual(self.sync("--check"), 1)
        self.assertEqual(self.state.read_bytes(), before)

    def test_pull_drops_private_fields_even_inside_model_lists(self):
        app = self.wanted["applicationUser"]
        app["cursorCreds"] = {"privateValue": "must not export"}
        app["aiSettings"]["accountOnly"] = "must not export"
        model = app["aiSettings"]["modelConfig"]["composer"]
        model["privateValue"] = "must not export"
        model["selectedModels"][0]["privateValue"] = "must not export"
        write_state(self.state, {
            preferences.APPLICATION_USER: app,
            "workbench.sideBar.size": 400,
            "unrelatedState": {"privateValue": "must not export"},
        })
        self.assertEqual(self.sync("--pull"), 0)
        text = self.source.read_text()
        self.assertNotIn("must not export", text)
        self.assertNotIn("privateValue", text)
        self.assertEqual(json.loads(text)["globalStorage"]["workbench.sideBar.size"], 400)

    def test_live_editor_refuses_writes_but_allows_pull_and_check(self):
        write_state(self.state, {preferences.APPLICATION_USER: {"cppEnabled": True}})
        before = self.state.read_bytes()
        self.running.return_value = True
        with self.assertRaisesRegex(RuntimeError, "Quit Cursor"):
            self.sync("--push")
        self.assertEqual(self.state.read_bytes(), before)
        self.assertEqual(self.sync("--pull"), 0)
        self.assertEqual(self.sync("--check"), 0)

    def test_unknown_source_fields_and_changed_storage_types_fail_without_writes(self):
        self.wanted["applicationUser"]["unmanaged"] = True
        self.source.write_text(json.dumps(self.wanted))
        with self.assertRaisesRegex(ValueError, "allowlist"):
            self.sync("--push")
        self.assertFalse(self.state.exists())
        write_state(self.state, {preferences.APPLICATION_USER: {"cppEnabled": "changed storage format"}})
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, "value type"):
            self.sync("--pull")
        self.assertEqual(self.source.read_bytes(), before)

    def test_pull_refuses_credential_like_values_without_replacing_saved_preferences(self):
        write_state(self.state, {preferences.APPLICATION_USER: {
            "composerState": {"agentBackendPreference": "sk-" + "x" * 24},
        }})
        before = self.source.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "credential"):
            self.sync("--pull")
        self.assertEqual(self.source.read_bytes(), before)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / "dotfiles"
        shutil.copytree(ROOT.parent, self.root, ignore=shutil.ignore_patterns("__pycache__"))
        self.home = self.directory / "home"
        self.home.mkdir()
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.installed = self.directory / "installed.txt"
        self.installed.write_text("")
        self.log = self.directory / "commands.txt"
        self.user = self.home / "Library/Application Support/Cursor/User"
        self.state = self.user / "globalStorage/state.vscdb"
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"),
                        PATH=f"{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin", PYTHONDONTWRITEBYTECODE="1")
        self.script("python3", f'#!/bin/sh\ncase "$1" in */cursor/preferences.py) exec "{sys.executable}" "$@";; *) exit 0;; esac\n')
        self.script("pgrep", "#!/bin/sh\nexit 1\n")
        self.script("code", f'#!/bin/sh\necho unexpected-code-call >> "{self.log}"\nexit 1\n')
        self.script("cursor", f'''#!{sys.executable}
from pathlib import Path
import sys
installed = Path({str(self.installed)!r})
log = Path({str(self.log)!r})
if sys.argv[1] == '--list-extensions':
    print(installed.read_text(), end='')
elif sys.argv[1] == '--install-extension':
    with installed.open('a') as handle:
        handle.write(sys.argv[2] + '\\n')
    with log.open('a') as handle:
        handle.write('cursor ' + sys.argv[2] + '\\n')
else:
    sys.exit(1)
''')
        (self.root / "rex/setup.sh").write_text("#!/bin/sh\nexit 0\n")

    def script(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)

    def run_installer(self, *args, expected=0):
        result = subprocess.run(["/bin/bash", str(self.root / "install.sh"), *args],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def test_new_mac_installs_cursor_profile_and_extensions_without_using_vscode(self):
        self.run_installer("--push")
        for name in ("settings.json", "keybindings.json"):
            self.assertEqual((self.user / name).read_bytes(), (ROOT / name).read_bytes())
        self.assertEqual(self.installed.read_text(), (ROOT / "extensions.txt").read_text())
        self.assertNotIn("unexpected-code-call", self.log.read_text())
        self.assertFalse((self.home / "Library/Application Support/Code").exists())
        self.assertIn("ok       Cursor extensions", self.run_installer("--check"))
        self.installed.write_text("")
        self.assertIn("missing  Cursor extension", self.run_installer("--check", expected=1))

    def test_pull_captures_current_cursor_settings_keybindings_extensions_and_preferences(self):
        self.run_installer("--push")
        settings = '{"editor.fontSize": 17}\n'
        keys = '[{"key":"cmd+l","command":"composerMode.agent"}]\n'
        (self.user / "settings.json").write_text(settings)
        (self.user / "keybindings.json").write_text(keys)
        self.installed.write_text("example.extension\n")
        current = read_state(self.state)
        current[preferences.APPLICATION_USER]["cppEnabled"] = True
        current[preferences.APPLICATION_USER]["accountOnly"] = "keep locally"
        write_state(self.state, current)
        self.run_installer("--pull")
        self.assertEqual((self.root / "cursor/settings.json").read_text(), settings)
        self.assertEqual((self.root / "cursor/keybindings.json").read_text(), keys)
        self.assertEqual((self.root / "cursor/extensions.txt").read_text(), "example.extension\n")
        saved = (self.root / "cursor/preferences.json").read_text()
        self.assertTrue(json.loads(saved)["applicationUser"]["cppEnabled"])
        self.assertNotIn("accountOnly", saved)
        self.assertNotIn("unexpected-code-call", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
