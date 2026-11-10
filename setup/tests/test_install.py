"""Installer safety checks using temporary homes; never install apps or change this Mac."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = ("setup/provision", "setup/dotfiles", "skills", "mods", "setup/preferences")


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        # Both paths deliberately contain spaces.
        self.repo = self.directory / "test repo"
        self.home = self.directory / "test home"
        self.home.mkdir()
        for name in ("setup/install.sh", "setup/lib/install-links.sh", "skills/install.sh", "mods/install.sh"):
            destination = self.repo / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, destination)
        self.claude = self.home / ".claude/skills"
        self.codex = self.home / ".agents/skills"
        self.env = {**os.environ, "HOME": str(self.home), "PATH": "/usr/bin:/bin"}
        self.add_item("skills", "example")
        self.add_item("mods", "example-mod")

    def add_item(self, component, name):
        marker = "SKILL.md" if component == "skills" else ".claude-plugin/plugin.json"
        path = self.repo / component / name / marker
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Example\n" if component == "skills" else '{"name":"example"}\n')

    def run_installer(self, *args, component=None, expected=0):
        script = self.repo / (component or "setup") / "install.sh"
        result = subprocess.run(["/bin/bash", str(script), *args], cwd=self.directory,
                                env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_links_only_marked_items_to_their_supported_agents(self):
        (self.repo / "skills/support files").mkdir()
        (self.repo / "mods/unfinished").mkdir()
        self.run_installer()
        for destination in (self.claude, self.codex):
            self.assertEqual(os.readlink(destination / "example"), str(self.repo / "skills/example"))
            self.assertFalse((destination / "support files").exists())
            self.assertFalse((destination / "unfinished").exists())
        self.assertEqual(os.readlink(self.claude / "example-mod"), str(self.repo / "mods/example-mod"))
        self.assertFalse((self.codex / "example-mod").exists())

    def test_repeat_leaves_existing_links_untouched(self):
        self.run_installer()
        link = self.claude / "example"
        before = link.lstat().st_mtime_ns
        self.run_installer()
        self.run_installer("--check")
        self.assertEqual(link.lstat().st_mtime_ns, before)

    def test_check_does_not_create_directories(self):
        self.run_installer("--check", expected=1)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_real_files_and_directories_are_preserved(self):
        self.claude.mkdir(parents=True)
        (self.claude / "example").write_text("keep this file")
        (self.claude / "example-mod").mkdir()
        (self.claude / "example-mod/keep").write_text("keep this directory")
        self.run_installer(expected=1)
        self.assertEqual((self.claude / "example").read_text(), "keep this file")
        self.assertEqual((self.claude / "example-mod/keep").read_text(), "keep this directory")

    def test_cleanup_is_scoped_and_check_does_not_remove_links(self):
        self.run_installer()
        targets = {
            "old-skill": self.repo / "skills/deleted",
            "old-mod": self.repo / "mods/deleted",
            "other-checkout": self.directory / "other repo/skills/deleted",
            "other-component": self.repo / "setup/dotfiles/deleted",
        }
        for name, target in targets.items():
            (self.claude / name).symlink_to(target)
        self.run_installer("--check", component="skills", expected=1)
        self.assertTrue(all((self.claude / name).is_symlink() for name in targets))
        self.run_installer(component="skills")
        self.assertFalse((self.claude / "old-skill").is_symlink())
        self.assertTrue((self.claude / "old-mod").is_symlink())
        self.run_installer(component="mods")
        self.assertFalse((self.claude / "old-mod").is_symlink())
        for name in ("other-checkout", "other-component"):
            self.assertTrue((self.claude / name).is_symlink())

    def test_moving_a_checkout_repoints_links_without_changing_the_old_target(self):
        previous = self.directory / "old repo/skills/example"
        previous.mkdir(parents=True)
        (previous / "SKILL.md").write_text("keep old checkout")
        self.claude.mkdir(parents=True)
        (self.claude / "example").symlink_to(previous)
        self.run_installer(component="skills")
        self.assertEqual(os.readlink(self.claude / "example"), str(self.repo / "skills/example"))
        self.assertEqual((previous / "SKILL.md").read_text(), "keep old checkout")

    def test_skill_mod_name_collision_does_not_replace_an_existing_link(self):
        self.add_item("mods", "example")
        self.claude.mkdir(parents=True)
        previous = self.directory / "unrelated"
        (self.claude / "example").symlink_to(previous)
        result = self.run_installer(expected=1)
        self.assertIn("conflict example", result.stdout)
        self.assertEqual(os.readlink(self.claude / "example"), str(previous))
        self.assertFalse((self.codex / "example").is_symlink())

    def test_unwritable_destination_is_reported_as_a_failure(self):
        (self.home / ".claude").write_text("not a directory")
        result = self.run_installer(component="skills", expected=1)
        self.assertIn("FAILED", result.stdout)
        self.assertNotIn(f"linked   {self.claude}", result.stdout)

    def stub_components(self):
        log = self.directory / "calls"
        self.env["FRONTIERISM_TEST_LOG"] = str(log)
        for component in COMPONENTS:
            path = self.repo / component / "install.sh"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'''#!/bin/sh
printf '%s:%s\\n' '{component}' "$*" >> "$FRONTIERISM_TEST_LOG"
test "${{FRONTIERISM_TEST_FAIL:-}}" != '{component}'
''')
            path.chmod(0o755)
        return log

    def test_full_check_continues_after_failure_and_checks_every_component(self):
        log = self.stub_components()
        self.env["FRONTIERISM_TEST_FAIL"] = "setup/provision"
        self.run_installer("--all", "--check", expected=1)
        self.assertEqual(log.read_text().splitlines(), [f"{name}:--check" for name in COMPONENTS])

    def test_full_install_stops_before_later_changes_when_a_component_fails(self):
        log = self.stub_components()
        self.env["FRONTIERISM_TEST_FAIL"] = "setup/dotfiles"
        self.run_installer("--all", expected=1)
        self.assertEqual(log.read_text().splitlines(), ["setup/provision:", "setup/dotfiles:"])

    def test_full_install_runs_in_order_and_exposes_newly_installed_commands(self):
        log = self.stub_components()
        provision = self.repo / "setup/provision/install.sh"
        provision.write_text(provision.read_text() + '''
mkdir -p "$HOME/.local/bin"
printf '#!/bin/sh\\nexit 0\\n' > "$HOME/.local/bin/frontierism-test-tool"
chmod +x "$HOME/.local/bin/frontierism-test-tool"
''')
        dotfiles = self.repo / "setup/dotfiles/install.sh"
        dotfiles.write_text(dotfiles.read_text() + "\nfrontierism-test-tool\n")
        self.run_installer("--all")
        self.assertEqual(log.read_text().splitlines(), [f"{name}:" for name in COMPONENTS])

    def test_invalid_arguments_fail_before_doing_any_work(self):
        for name in ("setup/provision/install.sh", "setup/dotfiles/install.sh"):
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, path)
        for component in (None, "setup/provision", "setup/dotfiles", "skills", "mods"):
            with self.subTest(component=component):
                self.run_installer("--check", "--push", component=component, expected=2)
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
