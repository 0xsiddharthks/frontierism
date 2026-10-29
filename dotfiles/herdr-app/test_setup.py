"""Exercise installation against private temporary homes, never the live app."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("herdr_setup", Path(__file__).with_name("setup.py"))
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.repo, self.app_home = root / "repo", root / "home/herdr-app"
        self.repo.mkdir()
        for relative in setup.managed_files():
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(setup.ROOT / relative, target)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(setup, "ROOT", self.repo))
        self.stack.enter_context(patch.dict(os.environ, {"HERDR_APP_HOME": str(self.app_home)}))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        self.stack.enter_context(patch.object(setup, "cli_path", return_value="fake-herdr-app"))
        self.stack.enter_context(patch.object(setup.time, "sleep"))
        self.calls = []
        self.running = None

        def command(cli, *args):
            self.calls.append(args)
            if args == ("status",):
                return subprocess.CompletedProcess(args, 0 if self.running else 1,
                                                   json.dumps(self.running), "no window")
            if args[:2] == ("do", "layout.switch"):
                self.running["layout"] = args[-1]
            if args[:2] == ("do", "overlay.close"):
                self.running["overlays"].remove(args[-1])
            return subprocess.CompletedProcess(args, 0, "{\"ok\":true}", "")

        self.stack.enter_context(patch.object(setup, "command", side_effect=command))

    def run_setup(self, mode=""):
        # The shell installer passes an empty argument for a plain invocation.
        with patch.object(sys, "argv", ["setup.py", mode]):
            return setup.main()

    def snapshot(self):
        return {str(p.relative_to(self.app_home)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.app_home.rglob("*") if p.is_file()}

    def test_fresh_home_and_repeat_apply_are_idempotent(self):
        self.assertEqual(self.run_setup(), 0)
        state = json.loads((self.app_home / "shared.json").read_text())
        self.assertEqual(state["layout"], "frontierism")
        self.assertEqual(state["frame.welcomed"], "skipped")
        self.assertEqual(state["agents.sort"], "priority")
        self.assertEqual(len([c for c in self.calls if c[0] == "check"]), len(setup.MODS))
        before = self.snapshot()
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.run_setup("--check"), 0)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(any(c[0] == "do" for c in self.calls))

    def test_plain_run_and_check_preserve_drift_then_push_keeps_backup(self):
        self.assertEqual(self.run_setup(), 0)
        path = self.app_home / "settings.json"
        original = b'{"zoom": 1.5}\n'
        path.write_bytes(original)
        before = self.snapshot()
        self.assertEqual(self.run_setup(), 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.run_setup("--check"), 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.run_setup("--push"), 0)
        backups = list(self.app_home.glob("settings.json.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        self.assertEqual(path.read_bytes(), (self.repo / "settings.json").read_bytes())

    def test_closed_window_activation_preserves_unrelated_state(self):
        self.app_home.mkdir(parents=True)
        state = {"layout": "main", "unrelated.preference": ["keep"], "agents.sort": "grouped"}
        setup.save_json(self.app_home / "shared.json", state)
        self.assertEqual(self.run_setup(), 0)
        result = json.loads((self.app_home / "shared.json").read_text())
        self.assertEqual(result["unrelated.preference"], ["keep"])
        self.assertEqual(result["agents.sort"], "grouped")
        self.assertEqual(result["layout"], "frontierism")
        self.assertEqual(len(list(self.app_home.glob("shared.json.bak-*"))), 1)

    def test_running_window_uses_commands_and_only_closes_welcome(self):
        self.assertEqual(self.run_setup(), 0)
        path = self.app_home / "shared.json"
        before = path.read_bytes()
        self.running = {"layout": "main", "errors": [], "overlays": ["frame-welcome", "other-dialog"]}
        self.calls.clear()
        self.assertEqual(self.run_setup("--push"), 0)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.running["overlays"], ["other-dialog"])
        self.assertIn(("do", "layout.switch", "--name", "frontierism"), self.calls)
        self.assertEqual([c for c in self.calls if c[:2] == ("do", "overlay.close")],
                         [("do", "overlay.close", "--id", "frame-welcome")])
        self.calls.clear()
        before = self.snapshot()
        self.assertEqual(self.run_setup("--check"), 0)
        self.assertEqual(self.calls, [("status",)])
        self.assertEqual(before, self.snapshot())

    def test_pull_excludes_runtime_state_other_mods_and_backup_files(self):
        self.assertEqual(self.run_setup(), 0)
        foreign = self.app_home / "mods/other/main.js"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("local session information")
        (self.repo / "layouts/frontierism.json.bak-example").write_text("not configuration")
        settings = self.app_home / "settings.json"
        settings.write_text('{"theme":"tokyo-night","zoom":1.25}\n')
        self.calls.clear()
        self.assertEqual(self.run_setup("--pull"), 0)
        self.assertEqual(settings.read_bytes(), (self.repo / "settings.json").read_bytes())
        self.assertFalse((self.repo / "shared.json").exists())
        self.assertFalse((self.repo / "mods/other").exists())
        self.assertFalse(any("bak-" in str(p) for p in setup.managed_files()))
        self.assertFalse(self.calls)

    def test_pull_refuses_credentials(self):
        self.assertEqual(self.run_setup(), 0)
        old = (self.repo / "settings.json").read_bytes()
        setup.save_json(self.app_home / "settings.json", {"token": "sk-" + "x" * 40})
        self.assertEqual(self.run_setup("--pull"), 1)
        self.assertEqual((self.repo / "settings.json").read_bytes(), old)

    def test_runtime_errors_fail_the_check(self):
        self.assertEqual(self.run_setup(), 0)
        self.running = {"layout": "frontierism", "errors": ["a mod failed"], "overlays": []}
        self.assertEqual(self.run_setup("--check"), 1)


class ProvisionTests(unittest.TestCase):
    """Run the real shell provisioner with local fake installers and no network."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.bin = self.home / ".local/bin"
        self.fake = self.root / "fake"
        self.log = self.root / "downloads"
        self.repo = Path(__file__).resolve().parents[2]
        self.fake.mkdir()
        for name in ("claude", "codex", "herdr"):
            self.script(self.bin / name, "exit 0")
        self.script(self.home / ".cargo/bin/rustup",
                    "printf '%s\\n' rust-src rustfmt clippy")
        self.script(self.home / ".oh-my-zsh/oh-my-zsh.sh", "exit 0")
        self.script(self.fake / "brew", '''
case "$1" in
  bundle)
    for arg in "$@"; do
      case "$arg" in --file=*) cat "$HERDR_TEST_BREWFILE" > "${arg#--file=}" ;; esac
    done ;;
  untrust|list) : ;;
  *) exit 2 ;;
esac
''')
        # Simulate the official app installer succeeding with its core missing:
        # provision must notice and invoke the standalone core installer too.
        for name, binary in (("app", "herdr-app"), ("core", "herdr-core")):
            self.script(self.root / f"{name}.sh", f'''
mkdir -p "$HOME/.local/bin"
printf '#!/bin/sh\\nexit 0\\n' > "$HOME/.local/bin/{binary}"
chmod +x "$HOME/.local/bin/{binary}"
''')
        self.script(self.fake / "curl", '''
for url in "$@"; do :; done
printf '%s\\n' "$url" >> "$HERDR_TEST_DOWNLOADS"
case "$url" in
  https://releases.herdr.dev/app/install.sh) cat "$HERDR_TEST_SCRIPTS/app.sh" ;;
  https://releases.herdr.dev/core/install.sh) cat "$HERDR_TEST_SCRIPTS/core.sh" ;;
  *) exit 2 ;;
esac
''')
        self.env = {**os.environ, "HOME": str(self.home),
                    "PATH": f"{self.fake}:{self.bin}:/usr/bin:/bin",
                    "HERDR_TEST_BREWFILE": str(self.repo / "provision/Brewfile"),
                    "HERDR_TEST_DOWNLOADS": str(self.log),
                    "HERDR_TEST_SCRIPTS": str(self.root)}

    @staticmethod
    def script(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nset -eu\n" + text + "\n")
        path.chmod(0o755)

    def provision(self, *args):
        return subprocess.run(["/bin/bash", str(self.repo / "provision/install.sh"), *args],
                              env=self.env, capture_output=True, text=True, timeout=30)

    def test_existing_tui_does_not_hide_missing_app_and_core(self):
        result = self.provision("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("missing  Herdr app", result.stdout)
        self.assertIn("missing  herdr-core", result.stdout)
        self.assertFalse(self.log.exists())
        result = self.provision()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),
                         ["https://releases.herdr.dev/app/install.sh",
                          "https://releases.herdr.dev/core/install.sh"])
        self.assertEqual(os.readlink(self.bin / "hc"), "herdr-core")
        before = self.log.read_bytes()
        result = self.provision("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.provision()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_bytes(), before)

    def test_existing_app_still_installs_missing_core(self):
        self.script(self.bin / "herdr-app", "exit 0")
        result = self.provision()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.log.read_text().splitlines(),
                         ["https://releases.herdr.dev/core/install.sh"])

    def test_another_hc_is_preserved_and_reported(self):
        self.script(self.bin / "herdr-app", "exit 0")
        self.script(self.bin / "herdr-core", "exit 0")
        self.script(self.bin / "hc", "exit 23")
        before = (self.bin / "hc").read_bytes()
        result = self.provision()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("conflict ~/.local/bin/hc", result.stdout)
        self.assertEqual((self.bin / "hc").read_bytes(), before)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
