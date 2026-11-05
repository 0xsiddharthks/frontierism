#!/usr/bin/env python3
"""Read-only, bounded filesystem and Git access for the /files mod."""

import codecs
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import threading

MAX_FILES = 20_000
MAX_PATH_BYTES = 1_500_000
MAX_PREVIEW_BYTES = 65_536
MAX_PREVIEW_LINES = 200


def git(root, *args):
    # Neither scanning nor previewing should run configured helper programs.
    return subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
        env={**os.environ, "GIT_LITERAL_PATHSPECS": "1", "GIT_TERMINAL_PROMPT": "0"},
    )


def checked(root, *args):
    result = git(root, *args)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip() or "Git command failed.")
    return result.stdout


def root_at(cwd):
    result = git(cwd, "rev-parse", "--show-toplevel")
    if result.returncode:
        raise ValueError("Open /files inside a Git working tree.")
    return Path(os.fsdecode(result.stdout).removesuffix("\n")).resolve()


def changes_at(root):
    fields = checked(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").split(b"\0")
    changes = []
    index = 0
    while index < len(fields) and fields[index]:
        field = fields[index]
        index += 1
        status = field[:2].decode("ascii")
        change = {"path": os.fsdecode(field[3:]), "status": status}
        if "R" in status or "C" in status:
            change["oldPath"] = os.fsdecode(fields[index])
            index += 1
        changes.append(change)
    return changes


def scan(cwd):
    root = root_at(cwd)
    paths = sorted(set(os.fsdecode(path) for path in checked(
        root, "ls-files", "--cached", "--others", "--exclude-standard", "-z",
    ).split(b"\0") if path))
    changes = changes_at(root)
    # Deleted files still belong in the tree, and renames use their current name.
    paths = sorted(set(paths) | {change["path"] for change in changes})
    loaded = []
    budget = 0
    for path in paths:
        budget += len(json.dumps(path))
        if len(loaded) >= MAX_FILES or budget > MAX_PATH_BYTES:
            break
        loaded.append(path)
    loaded_set = set(loaded)
    return {
        "root": str(root), "cwd": str(Path(cwd).resolve()), "paths": loaded,
        "changes": [change for change in changes if change["path"] in loaded_set],
        "total": len(paths), "truncated": len(loaded) < len(paths),
    }


def project_file(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts or ".git" in path.parts:
        raise ValueError("Choose a file inside the working tree.")
    full = root / path
    # Resolve parents too, so a directory symlink cannot escape the working tree.
    resolved = full.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("This link points outside the working tree; no preview is available.")
    if ".git" in resolved.relative_to(root).parts:
        raise ValueError("Git's internal files are not available in this browser.")
    return full


def text_preview(raw, kind, note="", clipped=False):
    if b"\0" in raw:
        return {"kind": kind, "source": "", "note": "Binary file; no text preview."}
    try:
        text = codecs.getincrementaldecoder("utf-8")().decode(raw, final=not clipped)
    except UnicodeDecodeError:
        return {"kind": kind, "source": "", "note": "This file is not UTF-8 text; no preview."}
    lines = text.splitlines()
    truncated = clipped or len(lines) > MAX_PREVIEW_LINES
    return {
        "kind": kind, "source": "\n".join(lines[:MAX_PREVIEW_LINES]),
        "note": " · ".join(part for part in [note, "Preview limited to 200 lines / 64 KiB." if truncated else ""] if part),
    }


def content(root, relative):
    full = project_file(root, relative)
    try:
        # Inspect before opening: never wait on a named pipe or read a device.
        info = full.stat()
    except FileNotFoundError:
        return {"kind": "content", "source": "", "note": "File is deleted or no longer exists. Choose Diff to see its changes."}
    if not stat.S_ISREG(info.st_mode):
        return {"kind": "content", "source": "", "note": "Not a regular file; no text preview."}
    with full.open("rb") as handle:
        raw = handle.read(MAX_PREVIEW_BYTES + 1)
    clipped = len(raw) > MAX_PREVIEW_BYTES
    return text_preview(raw[:MAX_PREVIEW_BYTES], "content", clipped=clipped)


def diff(root, relative):
    project_file(root, relative)
    change = next((item for item in changes_at(root) if item["path"] == relative), None)
    if change is None:
        return {"kind": "diff", "source": "", "note": "No uncommitted Git changes for this file."}
    if change["status"] == "??":
        preview = content(root, relative)
        return {**preview, "note": " · ".join(filter(None, ["Untracked file; showing its contents.", preview["note"]]))}
    has_head = git(root, "rev-parse", "--verify", "HEAD").returncode == 0
    paths = [relative] if "oldPath" not in change else [change["oldPath"], relative]
    args = ["diff", "--no-ext-diff", "--no-textconv", "--no-color"]
    # A diff against HEAD includes staged and unstaged edits together. With no
    # commits yet, show staged additions against the empty tree instead.
    args += ["HEAD"] if has_head else ["--cached"]
    args += ["--", *paths]
    # Bound stdout while Git is running, rather than collecting an entire huge diff.
    command = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          env={**os.environ, "GIT_LITERAL_PATHSPECS": "1"}) as process:
        # Bound wall time during read(), too: wait(timeout) alone only starts
        # counting once stdout has reached EOF or the byte limit.
        deadline = threading.Timer(15, process.kill)
        deadline.start()
        try:
            raw = process.stdout.read(MAX_PREVIEW_BYTES + 1)
            clipped = len(raw) > MAX_PREVIEW_BYTES
            if clipped:
                process.terminate()
            code = process.wait(timeout=10)
            if code and not clipped:
                raise ValueError("Git could not preview this diff. Try Content instead.")
        finally:
            deadline.cancel()
            if process.poll() is None:
                process.kill()
                process.wait()
    note = "Staged changes (repository has no commits yet)." if not has_head else "Compared with HEAD (staged + unstaged)."
    return text_preview(raw[:MAX_PREVIEW_BYTES], "diff", note, clipped)


def main(request):
    if request["op"] == "scan":
        return scan(request["cwd"])
    root = Path(request["root"]).resolve()
    if request["op"] == "preview":
        return (diff if request["mode"] == "diff" else content)(root, request["path"])
    raise ValueError("Unknown files operation.")


if __name__ == "__main__":
    try:
        answer = main(json.loads(sys.argv[1]))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        answer = {"error": str(error)}
    print(json.dumps(answer, ensure_ascii=True))
