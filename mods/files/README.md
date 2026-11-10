# /files

A native Claude Code pane for browsing the current Git working tree. It runs
locally, without a browser, server, or model request. It needs Git, Python 3.9 or
later, and Claude Code with mods enabled.

Run `./setup/install.sh` from the repository root, then `/reload-plugins` in an
existing Claude Code session. New sessions load `files@skills-dir` automatically.

## Use

Run `/files`, or `/files some/path` to start with a search.

- **All files** lists tracked files and untracked files that Git does not ignore.
- **Git changes** lists staged, unstaged, untracked, renamed, deleted, and
  conflicted paths. A changed file opens its diff against HEAD, combining staged
  and unstaged changes. Untracked files show their contents. Before the first
  commit, the diff shows staged additions.
- **This session** lists successful `Read`, `Edit`, `Write`, and `NotebookEdit`
  calls observed while this mod is loaded. Each file is marked `read` or
  `edited`; a later read does not erase an edited marker. Tracking continues
  while the pane is closed and survives plugin reloads within the running
  session. Shell-only activity is not attributed here; shell edits appear in
  Git changes. A restarted or resumed process starts a new activity record.

Search matches file names and paths, ignores case, and requires every
space-separated term to match. Matching folders expand automatically. Use the
folder buttons, Expand, or Collapse to browse without a search.

Press a file's name to preview it. Content and Diff switch the preview mode;
Previous lines and Next lines page through the preview. Files are read only,
with a maximum preview of 200 lines or 64 KiB. Binary files, non-UTF-8 files,
directories, and links outside the working tree have an explanatory message.

Press `[ ]` beside files to select them. Selection stays when you change views
or search. **Add N to prompt** appends absolute `@` references to your existing
draft without submitting it. Names containing spaces are quoted. Deleted paths
are added as explicitly labeled text because there is no file to attach.
Clear selection removes the selection, leaving the draft alone.

When the pane has keyboard focus, `a`, `g`, and `s` switch views, and `r`
refreshes. Use Tab and the arrow keys to reach controls, and Escape to return
to the prompt. Close closes the pane and stops its refresh timer.

The tree refreshes every ten seconds while open, and shortly after a file tool,
shell command, or completed turn. It uses the current working tree even if
Claude starts in a subdirectory or an independent Git worktree. Moving to
another working tree clears selections and previews.

The list is paged to keep the native pane small. A scan loads at most 20,000
paths or 1.5 MB of path data; an incomplete scan shows a notice, and search
covers the loaded paths. Submodules are listed as entries, not traversed.

## Check

```sh
claude plugin validate mods/files
claude plugin test mods/files
python3 -m unittest discover -s mods/files/tests -p 'test_*.py'
claude --plugin-dir mods/files
```

The mod tests exercise the controls on the terminal, desktop, VS Code, and
mobile surfaces. The Python tests use temporary Git repositories to check real
status output, worktrees, renames, combined diffs, and bounded previews.
