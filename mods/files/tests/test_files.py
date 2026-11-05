"""Exercise the reader against real temporary Git repositories."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("files", Path(__file__).resolve().parents[1] / "hooks/files.py")
files = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(files)


class FilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="files-mod-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.git("init", "-q")
        self.git("config", "user.name", "Files Test")
        self.git("config", "user.email", "files@example.com")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", "/dev/null")
        (self.root / "src").mkdir()
        (self.root / "src/app.py").write_text("old = 1\n")
        (self.root / "old name.txt").write_text("a file to rename\n")
        (self.root / ".gitignore").write_text("ignored/\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Initial files")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True).stdout

    def test_scan_uses_worktree_root_and_ignores_generated_files(self):
        (self.root / "ignored").mkdir()
        (self.root / "ignored/big.bin").write_bytes(b"\0")
        (self.root / "new file.txt").write_text("hello")
        answer = files.scan(self.root / "src")
        self.assertEqual(answer["root"], str(self.root))
        self.assertIn("new file.txt", answer["paths"])
        self.assertNotIn("ignored/big.bin", answer["paths"])
        self.assertIn({"path": "new file.txt", "status": "??"}, answer["changes"])

    def test_rename_and_delete_with_spaces_keep_their_real_paths(self):
        self.git("mv", "old name.txt", "new name.txt")
        (self.root / "src/app.py").unlink()
        answer = files.scan(self.root)
        self.assertIn({"path": "new name.txt", "oldPath": "old name.txt", "status": "R "}, answer["changes"])
        self.assertIn({"path": "src/app.py", "status": " D"}, answer["changes"])
        self.assertIn("src/app.py", answer["paths"])
        self.assertIn("rename from old name.txt", files.diff(self.root, "new name.txt")["source"])
        self.assertIn("-old = 1", files.diff(self.root, "src/app.py")["source"])

    def test_diff_includes_staged_and_unstaged_edits_and_literal_pathspecs(self):
        (self.root / "src/app.py").write_text("staged = 2\n")
        self.git("add", "src/app.py")
        (self.root / "src/app.py").write_text("current = 3\n")
        source = files.diff(self.root, "src/app.py")["source"]
        self.assertIn("-old = 1", source)
        self.assertIn("+current = 3", source)
        self.assertNotIn("+staged = 2", source)
        (self.root / "[a].txt").write_text("literal")
        self.assertIn("literal", files.diff(self.root, "[a].txt")["source"])

    def test_preview_bounds_binary_large_and_nonregular_files(self):
        (self.root / "binary").write_bytes(b"image\0data")
        self.assertIn("Binary", files.content(self.root, "binary")["note"])
        (self.root / "large").write_text("line\n" * 100_000)
        preview = files.content(self.root, "large")
        self.assertEqual(len(preview["source"].splitlines()), 200)
        self.assertIn("limited", preview["note"])
        self.assertIn("Not a regular file", files.content(self.root, "src")["note"])
        self.assertIn("deleted", files.content(self.root, "missing")["note"])

    def test_preview_refuses_outside_symlinks_and_git_internals(self):
        (self.root / "outside").symlink_to(self.root.parent)
        (self.root / "git-config-link").symlink_to(self.root / ".git/config")
        for path in ["../outside.txt", "/etc/hosts", "outside/a.txt", ".git/config", "git-config-link"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                files.content(self.root, path)

    def test_a_utf8_character_at_the_preview_boundary_is_not_replaced(self):
        preview = files.text_preview(b"a" * (files.MAX_PREVIEW_BYTES - 1) + b"\xc3", "content", clipped=True)
        self.assertNotIn("\ufffd", preview["source"])
        self.assertEqual(len(preview["source"]), files.MAX_PREVIEW_BYTES - 1)
        self.assertIn("limited", preview["note"])

    def test_a_large_diff_is_bounded_and_does_not_run_external_diff_helpers(self):
        (self.root / "src/app.py").write_text("new = 2\n" * 100_000)
        self.git("config", "diff.external", "a-command-that-must-not-run")
        preview = files.diff(self.root, "src/app.py")
        self.assertIn("+new = 2", preview["source"])
        self.assertEqual(len(preview["source"].splitlines()), 200)
        self.assertIn("limited", preview["note"])

    def test_a_separate_git_worktree_is_not_the_main_checkout(self):
        worktree = self.root / "separate tree"
        self.git("worktree", "add", "-qb", "test-worktree", str(worktree))
        (worktree / "src/app.py").write_text("worktree only\n")
        answer = files.scan(worktree / "src")
        self.assertEqual(answer["root"], str(worktree))
        self.assertIn("+worktree only", files.diff(worktree, "src/app.py")["source"])
        self.assertEqual((self.root / "src/app.py").read_text(), "old = 1\n")

    def test_an_unborn_repository_can_show_staged_additions(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "first.txt").write_text("first\n")
            subprocess.run(["git", "-C", str(root), "add", "first.txt"], check=True)
            self.assertIn("+first", files.diff(root, "first.txt")["source"])


if __name__ == "__main__":
    unittest.main()
