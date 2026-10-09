#!/usr/bin/env python3
"""List the paths and code names in the agent-context guides that the source repos no longer have.

Checks each backticked path, and each snake_case, SCREAMING_CASE, camelCase or kebab-case name,
against every repo's origin default branch and the mysten repo's working tree. It prints what it
couldn't find, what it found only in repos that weren't just fetched, and names found only in the
SDK or frontend, whose bindings lag hashi. It skips commands, flags and fenced blocks, and accepts a
name or bare file name found anywhere, so its hits are leads and a clean run proves little. It only
reads, so fetch the repos first.

usage: stale-refs.py [guide ...] [--repo NAME=PATH ...]
"""

import argparse
import copy
import fnmatch
import glob
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
MYSTEN = HOME / "Developer/0xsiddharthks/mysten"
AGENT_CONTEXT = MYSTEN / "agent-context"
REPOS = {
    "hashi": HOME / "Developer/MystenLabs/hashi",
    "sui-operations": HOME / "Developer/MystenLabs/sui-operations",
    "ts-sdks": HOME / "Developer/MystenLabs/ts-sdks",
    "hashi-frontend": HOME / "Developer/MystenLabs/hashi-frontend",
    "kyoto": HOME / "Developer/0xsiddharthks/kyoto",
}
# Hashi's bindings in the SDK and frontend lag hashi, so a name found only there was probably
# removed from hashi. The rest of ts-sdks is the Sui SDK and counts like any other repo.
BINDINGS = "ts-sdks/packages/hashi"
DOWNSTREAM = {BINDINGS, "hashi-frontend"}
# A segment that makes `a/b` a GitHub slug, an API path or a git ref rather than a file.
NOT_PATHS = {"origin", "upstream", "refs", "MystenLabs", "0xsiddharthks", "2140-dev", "xdevplatform"}
FILE_EXT = re.compile(r"\.(rs|move|toml|ya?ml|mdx?|sh|py|go|tsx?|m?js|json|proto|graphql|lock)$")
# Code files: a mention in a comment doesn't mean the file still exists.
SOURCE_EXT = re.compile(r"\.(rs|move|sh|py|go|tsx?|m?js|proto|graphql)$")
HOST = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)*\.(io|com|org|net|dev|app|xyz|ai)(/|$)")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
TOKEN = r"[A-Za-z_][A-Za-z0-9_-]*"
KEBAB = re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)+")
CODE = ["--", ".", ":!*.md", ":!*.mdx"]


def git(repo, *args, stdin=None):
    return subprocess.run(["git", "-C", str(repo), *args], input=stdin, capture_output=True, text=True)


class Source:
    """One repo's files at a ref (or its working tree), with every path suffix indexed."""

    def __init__(self, name, root, files, ref=None, fresh=True):
        self.name, self.root, self.ref, self.fresh = name, root, ref, fresh
        self.spec = CODE
        dirs = {"/".join(f.split("/")[:i]) for f in files for i in range(1, f.count("/") + 1)}
        self.paths = sorted(set(files) | dirs)
        self.suffixes, self.stems = set(), set()
        for p in self.paths:
            parts = p.split("/")
            self.suffixes.update("/".join(parts[i:]) for i in range(len(parts)))
            self.stems.add(parts[-1].split(".")[0])
        self._texts = self._tokens = None

    def has(self, path):
        if any(c in path for c in "*?["):
            if any(fnmatch.fnmatchcase(p, path) or fnmatch.fnmatchcase(p, "*/" + path) for p in self.paths):
                return True
        elif path in self.suffixes:
            return True
        return self.local(path)

    def local(self, path):
        """Whether the checkout has untracked or ignored files at path, like local settings or worktrees.

        Tracked files don't count: a stale checkout still has files its default branch deleted.
        """
        matches = glob.glob(str(self.root / path))
        return any(git(self.root, "ls-files", "--error-unmatch", "--", m).returncode != 0 for m in matches)

    # Content checks read only code and config. Prose is left out: docs lag the code, and the
    # guides would otherwise match themselves.

    def texts(self):
        if self._texts is None:
            self._texts = []
            for f in self.paths:
                path = self.root / f
                if f.endswith((".md", ".mdx")) or not path.is_file():
                    continue
                if path.stat().st_size < 2_000_000:
                    self._texts.append(path.read_text(errors="ignore"))
        return self._texts

    def tokens(self):
        """Every identifier and kebab-case run in the code, plus the words inside each run."""
        if self._tokens is None:
            if self.ref:
                runs = git(self.root, "grep", "-I", "-h", "-o", "-E", TOKEN, self.ref, *self.spec).stdout.split()
            else:
                runs = [r for t in self.texts() for r in re.findall(TOKEN, t)]
            self._tokens = set(runs)
            self._tokens.update(part for run in self._tokens.copy() if "-" in run for part in run.split("-"))
        return self._tokens

    def contains(self, strings):
        if not self.ref:
            return {s for s in strings if any(s in t for t in self.texts())}
        patterns = "\n".join(strings) + "\n"
        out = git(self.root, "grep", "-I", "-h", "-o", "-F", "-f", "-", self.ref, *self.spec, stdin=patterns)
        return set(out.stdout.splitlines()) & strings


def load_git(name, root):
    for ref in ("origin/HEAD", "origin/main", "origin/master"):
        sha = git(root, "rev-parse", "--verify", "-q", ref + "^{commit}").stdout.strip()
        if sha:
            break
    else:
        return None, f"{name:15} no origin default branch in {root}"
    branch = git(root, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD").stdout.strip() or ref
    # A failed fetch still empties FETCH_HEAD and bumps its time, so a fresh one must name the head.
    # Each worktree keeps its own FETCH_HEAD.
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    ages = [
        (time.time() - f.stat().st_mtime) / 3600
        for f in [common / "FETCH_HEAD", *common.glob("worktrees/*/FETCH_HEAD")]
        if f.is_file() and sha in f.read_text(errors="ignore")
    ]
    fresh = bool(ages) and min(ages) <= 24
    state = f"fetched {min(ages):.1f}h ago" if fresh else "no fetch of this head in the last 24h  <- fetch first"
    files = git(root, "ls-tree", "-r", "-z", "--name-only", ref).stdout.split("\0")
    source = Source(name, root, [f for f in files if f], ref, fresh)
    return source, f"{name:15} {branch} {sha[:9]}  ({state})"


def load_mysten():
    # Tracked and untracked files, plus the gitignored artifacts the guides point to. Other
    # ignored trees (target/, the local hashi/ study notes) could hide a dead path, so skip them.
    out = git(MYSTEN, "ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
    files = [f for f in out.split("\0") if f]
    for dirpath, dirnames, filenames in os.walk(MYSTEN / "artifacts"):
        dirnames[:] = [d for d in dirnames if d not in {".git", "target", "node_modules"}]
        files += [os.path.relpath(os.path.join(dirpath, f), MYSTEN) for f in filenames]
    return Source("mysten", MYSTEN, files), f"{'mysten':15} working tree"


def expand_braces(token):
    m = re.search(r"\{([^{}]*,[^{}]*)\}", token)
    if not m:
        return [token]
    return [x for alt in m.group(1).split(",") for x in expand_braces(token[: m.start()] + alt + token[m.end() :])]


def is_code_name(word):
    return len(word) >= 4 and WORD.fullmatch(word) and ("_" in word or re.search(r"[a-z][A-Z]", word))


def classify(token):
    """Yield the (kind, value) pairs worth checking in one backticked token."""
    t = token.strip()
    metric = re.fullmatch(r"([A-Za-z_]\w*)\{[^{}]*\}", t)
    if metric:
        t = metric.group(1)
    if re.search(r"\s", t):
        # A command or a phrase: check only the words in it that look like paths.
        for word in t.split():
            if "/" in word:
                yield from classify(word)
        return
    t = t.removesuffix("()")
    if t.startswith("@"):
        t = re.sub(r"(?<=.)@[^/]*$", "", t)  # an npm package without its version
    if re.search(r"[<>$|=\"'\\()]|\.\.\.|…", t) or t.startswith("-"):
        return
    if "/" in t or FILE_EXT.search(t):
        t = re.sub(r"^(\.\.?/)+", "", t.rstrip("/"))
        if not t or ":" in t or re.fullmatch(r"\.\w+", t):
            return  # also skips image tags and `ref:path`
        if not t.startswith(("~", str(HOME))):
            segments = t.split("/")
            if t.startswith("/") or HOST.match(t) or NOT_PATHS.intersection(segments):
                return
            if re.fullmatch(r"[A-Z][A-Za-z]*", segments[0]) and not FILE_EXT.search(t):
                return  # an RPC method such as `LedgerService/GetObject`
        for candidate in expand_braces(t):
            yield "path", candidate
        return
    t = t.removesuffix("*")  # `hashi_monitor_*` names a prefix
    if KEBAB.fullmatch(t):
        yield "kebab", t
        return
    for word in re.split(r"::|\.", t):
        if is_code_name(word):
            yield "name", word


def found_in(kind, value, sources):
    """The names of the sources that have this path or name (or "local" for files on this Mac)."""
    if kind == "path":
        if value.startswith(("~", str(HOME))):
            return {"local"} if glob.glob(os.path.expanduser(value)) else set()
        hits = {s.name for s in sources.values() if s.has(value)}
        first, _, rest = value.partition("/")
        if rest and first in sources and sources[first].has(rest):
            hits.add(first)
        # A repo, or a leftover directory next to one, named relative to ~/Developer.
        if not hits and "/" not in value and glob.glob(str(HOME / "Developer" / "*" / value)):
            hits.add("local")
        return hits
    forms = {value}
    hits = set()
    if kind == "kebab":
        # A CLI subcommand or config key is often derived from a Rust name, and a crate, script
        # or artifact is often named by its directory or file.
        forms |= {value.replace("-", "_"), "".join(p.capitalize() for p in value.split("-"))}
        hits = {s.name for s in sources.values() if value in s.stems}
        if glob.glob(str(HOME / "Developer" / "*" / value)):
            hits.add("local")
    for s in sources.values():
        tokens = s.tokens()
        if forms & tokens or value.endswith("_") and any(t.startswith(value) for t in tokens):
            hits.add(s.name)
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("guides", nargs="*", help="guide files or names (default: every guide)")
    parser.add_argument("--repo", action="append", default=[], metavar="NAME=PATH", help="add or override a repo")
    args = parser.parse_args()

    repos = dict(REPOS)
    for spec in args.repo:
        name, _, path = spec.partition("=")
        repos[name] = Path(os.path.expanduser(path))
    guides = []
    for g in args.guides or sorted(p.name for p in (AGENT_CONTEXT / "memory").glob("*.md")):
        path = Path(g) if os.sep in g else AGENT_CONTEXT / "memory" / (g if g.endswith(".md") else g + ".md")
        if not path.is_file():
            sys.exit(f"no such guide: {g}")
        guides.append(path)

    sources = {}
    print("Sources:")
    for name, root in repos.items():
        if not (root / ".git").exists():
            print(f"  {name:15} missing at {root}")
            continue
        source, line = load_git(name, root)
        print("  " + line)
        if source:
            sources[name] = source
    sources["mysten"], line = load_mysten()
    print("  " + line)
    repo, _, subdir = BINDINGS.partition("/")
    if repo in sources:
        bindings = copy.copy(sources[repo])
        bindings.name, bindings.spec = BINDINGS, ["--", subdir, ":!*.md", ":!*.mdx"]
        sources[repo].spec = CODE + [":!" + subdir]
        sources[BINDINGS] = bindings

    refs = []
    for guide in guides:
        fenced = False
        for n, text in enumerate(guide.read_text().splitlines(), 1):
            if text.lstrip().startswith("```"):
                fenced = not fenced
            elif not fenced:
                for token in re.findall(r"`([^`\n]+)`", text):
                    refs += [(guide.name, n, kind, value) for kind, value in classify(token)]

    found = {key: found_in(*key, sources) for key in {(kind, value) for _, _, kind, value in refs}}
    # A path missing from every tree may be one the code builds at runtime (an S3 prefix, a
    # generated config, an image or action name), so accept it if it appears verbatim.
    lost = {v for (kind, v), hits in found.items() if kind == "path" and not hits and not SOURCE_EXT.search(v)}
    for s in sources.values():
        for v in s.contains(lost) if lost else ():
            found[("path", v)].add(s.name)

    stale = {s.name for s in sources.values() if not s.fresh}
    missing, downstream = [], []
    for guide, n, kind, value in refs:
        hits = found[(kind, value)]
        if not hits - stale:
            note = f"  (only in stale {', '.join(sorted(hits))})" if hits else ""
            missing.append(f"  {guide}:{n}  {kind}  {value}{note}")
        elif kind != "path" and hits <= DOWNSTREAM:
            downstream.append(f"  {guide}:{n}  {kind}  {value}  ({', '.join(sorted(hits))})")

    print(f"\nChecked {len(refs)} references in {len(guides)} guides.")
    if missing:
        print(f"\nNot found ({len(missing)}; a path may be relative to a directory named nearby):")
        print("\n".join(missing))
    if downstream:
        print(f"\nFound only in the SDK or frontend ({len(downstream)}; a hashi name here was probably removed):")
        print("\n".join(downstream))
    if not missing and not downstream:
        print("Nothing to check by hand.")


if __name__ == "__main__":
    main()
