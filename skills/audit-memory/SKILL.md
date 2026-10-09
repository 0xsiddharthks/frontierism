---
name: audit-memory
description: Audit Sid's agent-context guides against the current code. Re-verifies every factual line against freshly fetched repos, looks at what merged since the last audit for gaps a new task would trip on, restructures where that helps, edits the guides in place, and reports what changed plus the problems it found outside the guides. Commits only after Sid approves. Takes guide names to narrow the scope. Use only when Sid runs /audit-memory or explicitly asks for it.
argument-hint: "[guide ...] [since YYYY-MM-DD] [notes]"
disable-model-invocation: true
---

# Audit memory

Arguments: `$ARGUMENTS` (if that wasn't substituted, the text after the skill name in Sid's message).

The guides are in `/Users/siddharthks/Developer/0xsiddharthks/mysten/agent-context/memory/`. `AGENTS.md` is the index every session loads, and the topic guides are the files it points to. They drift as code merges. This skill brings them back in line with the code and adds what new tasks need, so an agent starts each task with good pointers.

They should be a starting point, not a spec. A guide that explains how everything works goes stale and boxes agents in, and they stop thinking from first principles. A line earns its place only if:

- it stays true for months (for IDs, SHAs, PCRs, versions and counts that change, it says where to look them up);
- an agent couldn't quickly learn it from the code, docs or `--help`;
- removing it would cause a mistake: it's a trap, an invariant, one of Sid's rules, or a pointer that saves real search time.

Prefer where something lives and why it matters over how it works.

## 1. Scope and ground rules

- Guide names in the arguments, with or without `.md`, narrow the scope. Without any, audit every guide, `AGENTS.md` included. `since YYYY-MM-DD` overrides the baseline, and the rest is guidance from Sid for this run.
- Otherwise each guide's baseline is its own `last audited:` date (the first date in its comment), and the survey in step 3 starts from the oldest one in scope.
- Read `AGENTS.md` first if your session didn't load it. Its safety and evidence rules apply throughout.
- Only files in `agent-context/` change, besides your own scratch files and worktrees. Everything else is read-only: no pushes, GitHub writes, or cluster, cloud, chain or Vercel changes. A read-only live check is fine when a line describes live state; print the kube context first.
- Run `git status --short -- agent-context/` in the mysten repo before you start. If a file you'll edit already has uncommitted changes, ask Sid before touching it; they belong to another session.
- Don't print files that can hold secrets (`.env*`, `validator.toml`, stack configs); grep for the key you need.

## 2. Get fresh sources

- `git fetch origin` in every repo `stale-refs.py` checks (step 3), and in any other repo the guides in scope cite. Then read at `origin/<default branch>`, never at the working tree of someone's checkout, and note each head's SHA for the report. If a fetch fails, say so; don't audit against a stale ref silently.
- `git show <ref>:<path>`, `git grep <pattern> <ref>` and `git ls-tree -r <ref>` read at the head without a checkout. Add a detached worktree at the head, under that repo's `.claude/worktrees/`, only to run something or to give subagents plain file reads, and remove it when you're done.
- If a git command is refused outside your checkout, or your sandbox blocks the network or writes outside your workspace, ask Sid to allow it or to rerun from a session started in the mysten repo.

## 3. Survey what changed

- List what merged since the baseline: `git log --since='<baseline> 00:00' --format='%h %ad %s' --date=short <ref>` (a bare date means that date at the current time of day) in hashi, hashi-frontend and kyoto, with `-- packages/hashi` in ts-sdks, `-- '*hashi*' '*guardian*'` in sui-operations and `-- scripts` in mysten. Group it by area, and note structural changes: crates, modules, Move modules, workflows, design docs, CLI commands or scripts that were added, moved or removed.
- Run `python3 /Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/audit-memory/stale-refs.py [guide ...]`. It checks the backticked paths and code names in the guides against every repo, and prints what it couldn't find, what it found only in a repo that wasn't freshly fetched, and names found only in the SDK or frontend, whose copies lag hashi. It skips commands, flags and fenced blocks, and accepts a name or bare file name found anywhere, so its hits are leads and a clean run proves little.
- Notes in `agent-context/inbox/` are leads too. Leave them for `/learn`.

## 4. Audit

Run two passes, accuracy and coverage, then look at the structure. Spend effort where drift is likely: lines about areas with commits since the baseline, or hit in step 3, get a full check. The rest still get checked, just faster.

- **Accuracy.** If your tool has subagents, give each guide to one with fresh context rather than a fork of yours. Split guides over about 120 lines at `##` boundaries, and if your tool runs only a few subagents at once, pair up small guides. Brief each from `/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/audit-memory/auditor-brief.md`: fill in every field, and pass on the commits and leads for its area, Sid's notes, and your own questions. Without subagents, work through the brief yourself, one guide at a time.
- **Coverage.** Pick 3-5 PRs merged since the baseline, in different areas, favoring ones with long review threads or follow-up fixes. For each, write down from its title and linked issue alone where the guides would send you and what they'd warn about. Then read the PR, its review threads and any follow-up fix, and compare. A durable trap the guides missed is a candidate line. The brief's coverage section runs this in a subagent.
- **Structure.** Compare the code's layout with `hashi-code-map.md`: an area without a pointer is a gap. Check that each trigger in `AGENTS.md` still matches its guide. Ask whether a guide that doesn't exist yet would save most tasks their first half hour, as the code map does, and how a guide over about 200 lines should split.

## 5. Decide and edit

- Reports are leads. Check a finding yourself at the recorded heads before acting on it. Prefer the real artifact (a built binary's `--help`, the rendered config, a read-only live query) to a reading of the code, but build at most once, in your own session, and only when the code can't settle a claim that matters.
- Sid's rules (never, always, ask me) stay, even when a report questions one. Update a name a rule refers to if it changed, and report rules that conflict with each other or with a script.
- For each line: keep it, update it, delete it (no longer true, or not worth its tokens), merge a duplicate into the most canonical guide, or move it to a better one. Point to another repo's `CLAUDE.md`, `AGENTS.md` or runbook instead of restating it.
- Add only what clears the bar above. When a guide nears its size limit, cut something weaker instead of growing it.
- Write only what you verified: no speculation, estimates or hedges. Leave a line you couldn't verify as it was, and list it in the report.
- Edit in place with small, targeted edits; never rewrite a whole file. Match the file: short imperative bullets, nested bullets indented 2 spaces, and Sid's voice for his rules.
- Give a new guide a one-line pointer under "Topic guides" in `AGENTS.md` saying when to read it.
- Set `last audited:` to today in each guide you audited in full. After a partial audit, keep the date and add what you re-checked, e.g. `2026-09-12 (repos re-checked 2026-09-28)`.
- Don't fix anything outside `agent-context/`, such as code bugs, stale design docs or code comments, config drift or broken scripts. Collect them for the report.

## 6. Check

- Re-run `stale-refs.py` on the guides you edited; nothing you added should show up.
- Keep `AGENTS.md` under about 120 lines, and name any guide over about 200 as a split candidate.
- Check the wiring: `AGENTS.md` lists every guide in `memory/`, and each guide section a skill cites by name (such as "Before pushing" in `hashi-development.md`) still exists.
- No credential-shaped strings, secrets or volatile values went in.
- Read the whole diff (`git diff -- agent-context/`) end to end, as a reviewer would.

## 7. Report and wait

- One line on scope: which guides, checked against which heads (repo and short SHA), and the net line change.
- The wrong or stale claims you fixed, most consequential first.
- What's new: guides, sections, and invariants that could do real damage if missed.
- Deletions Sid should double-check.
- Problems outside the guides, each with its evidence and the likely fix. Call a code bug suspected unless you reproduced it the way CI runs, and for live state, name the layer your evidence proves.
- Loose ends: split candidates, lines you couldn't verify, partial audits, and inbox notes the audit already covered, so `/learn` can drop them.

Then stop and ask whether to commit. On Sid's go, re-run `git status --short -- agent-context/` in the mysten repo, and if a file you changed also holds edits you didn't make, ask first. Then commit and push: `git add -- <files>`, `git commit -m "[agent-context] <what the audit changed>" -- <files>`, `git push`. Commit only your files, and never bypass signing or hooks. If the push is rejected, stop and tell Sid.
