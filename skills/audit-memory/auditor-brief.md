# Auditor brief

`audit-memory` gives this to each subagent, or follows it itself. Fill in every `<...>`, drop lines that don't apply, and add the questions you already have. A subagent sees only the brief, so it has to stand alone.

## Accuracy

You're auditing one of Sid's agent guides: topic files in `/Users/siddharthks/Developer/0xsiddharthks/mysten/agent-context/memory/` that agents read before a kind of work. They cover hashi (Mysten Labs' Bitcoin bridge on Sui), its infrastructure, and Sid's tools. This guide was last audited <its date>; today is <today>.

Your assignment: `<guide>`, lines <from>-<to> (<sections>). Read the whole guide first, and skim the other guides in that folder so you flag duplicates instead of proposing them.

Read-only: don't edit, create or delete any file, and don't build. No pushes, GitHub writes, or cluster, cloud, chain or Vercel changes. Run git as plain single commands (no pipes, loops, `$(...)` or `&&` chains), because some sessions refuse anything else. Don't print files that can hold secrets (`.env*`, `validator.toml`, stack configs); grep for the key you need.

Sources, each at a freshly fetched head:

- <repo>: `<path>` at `<ref>` (`<sha>`)<, checked out at `<worktree>` for plain file reads>
- Read-only `gh` for PR context, e.g. `gh pr view <n> --repo <owner>/<repo> --json title,body,files`

Merged in this area since <its date>:

<short sha and title, one per line>

Leads: <stale-refs.py hits in this range, inbox notes, your questions>

Sid's notes for this run: <notes, or drop this line>

How to judge each line:

- The guides are pointers and hard-won gotchas for an agent starting a new task, not a spec. Sid doesn't want so much detail that agents get boxed in and stop thinking from first principles. A line earns its place only if it stays true for months, an agent couldn't quickly learn it from the code, docs or `--help`, and removing it would cause a mistake. Volatile values (IDs, SHAs, PCRs, versions, counts that change) should become "where to look it up".
- Rules (never, always, don't, ask me) are Sid's. Don't judge them; check only that what they refer to still exists under that name.
- Verify factual lines (paths, commands, flags, config keys, names, constants, behavior) at the heads above, citing file:line or a command and its output. A matching name doesn't prove the behavior, so follow the code path. For CLI or build behavior, read the definitions (clap types, Makefile, workflows); if they can't settle it, say what would.
- Design docs and runbooks lag the code. They're leads, not evidence.
- Mark a line you can't check (live systems, history) UNVERIFIABLE, and keep it unless something contradicts it. A failed query proves nothing.

Also look for what's missing: durable pointers, invariants and failure modes in this area that changed since <its date>, or that a new task here would trip on. Propose pointers (where it lives, why it matters), not explanations.

Return your report as your final message:

1. Headline: the few findings that matter most.
2. Per line: `L<n> STATUS: evidence. Replacement text, if any.` STATUS is KEEP, UPDATE, DELETE, MERGE (with which line), MOVE (to which guide) or UNVERIFIABLE. Keep KEEP entries short, and write replacement text in the guide's style: short imperative bullets, nested bullets indented 2 spaces.
3. MISSING: proposed lines, most important first, each with its evidence and target section.
4. Outside the guides: code bugs, stale design docs or code comments, config drift, broken scripts, each with its evidence. Don't fix them.
5. Duplicates across guides.

## Coverage

Use the opening, read-only and sources paragraphs above, then:

Your assignment: judge whether the guides would get a fresh agent up to speed on real work, using these PRs merged since <baseline>: <PR links>

For each PR:

1. From its title and linked issue alone, use the guides to write down where you'd start, which invariants you'd protect and what you'd test, following the triggers in `AGENTS.md` to pick guides.
2. Then read the body, the diff, the review threads and any later PR that fixed it. `gh pr view` misses inline threads; get them with `gh api graphql -F owner=<owner> -F name=<repo> -F number=<n> -F query=@/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/pr-address-feedback/review-threads.graphql`.
3. Compare: what did the guides get right, and what did reviews or follow-ups have to fix that a guide line could have warned about?

Hold proposals to the same bar as the accuracy audit: durable, not quickly learnable, and costly to miss.

Return your report as your final message:

1. Per PR: what the guides got right and what they missed.
2. Proposed lines, most important first, each with its evidence and target guide and section.
3. Outside the guides, as in the accuracy report.
