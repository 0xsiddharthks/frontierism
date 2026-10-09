---
name: learn
description: Save durable lessons from this session, and notes waiting in the agent-context inbox, into Sid's agent-context guides after he approves each change. Use only when Sid runs /learn or explicitly asks for it.
disable-model-invocation: true
---

# Learn

The guides live in `/Users/siddharthks/Developer/0xsiddharthks/mysten/agent-context/memory/`. `AGENTS.md` is the index every session loads, and the other files are the topic guides it points to. Nothing changes without Sid's approval.

Arguments: `$ARGUMENTS` (if that wasn't substituted, the text after the skill name in Sid's message). If they start with `audit`, the audit has its own skill: follow `/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/audit-memory/SKILL.md` with the rest of the arguments instead.

## 1. Gather candidates

- From this conversation: rules or corrections Sid gave, gotchas that cost time, procedures that worked, and guide lines that turned out wrong or missing.
- From `/Users/siddharthks/Developer/0xsiddharthks/mysten/agent-context/inbox/`: notes the hook saved when a Claude session tried to write auto memory. Each note's first line names its session, working directory and transcript.
- Any file other than `MEMORY.md` in `~/.claude/projects/-Users-siddharthks-Developer-MystenLabs*/memory/`. These are writes that got past the hook. Delete them with `rm` once handled, since the hook blocks Write and Edit there.
- Only if Sid asks: his messages from the last 7 days of MystenLabs transcripts (`~/.claude/projects/-Users-siddharthks-Developer-MystenLabs*/*.jsonl`), for rules nobody saved. Use a subagent, and skip pasted logs over about 4 KB.

If this session was compacted (Claude only), recover Sid's messages from the transcript:

```sh
t=$(find ~/.claude/projects -maxdepth 2 -name '${CLAUDE_SESSION_ID}.jsonl' | head -1)
jq -r 'select(.type == "user" and (.message.content | type) == "string") | .message.content' "$t"
```

## 2. Keep only real lessons

Keep a candidate only if all of these hold:

- It stays true for months. No PR or deploy status, IDs, SHAs, PCRs, rosters, or details of this one task.
- An agent couldn't quickly learn it from the code, docs or `--help`.
- Something outside the agent backs it: Sid's words, a command's result, or a source you checked just now. Re-check factual claims before proposing them.
- Removing it would cause a mistake.

Closing remarks ("leave it", "looks good") and preferences for this one task aren't lessons.

Prefer fewer, stronger lessons. If a candidate only just passes these tests, skip it — and when you do propose several, say which is weakest.

## 3. Place each lesson

- Use the guide whose trigger in the `AGENTS.md` topic list matches. Put a rule in `AGENTS.md` itself only if it applies to nearly all work.
- Search the guides for overlap first, then pick one action: update an existing line, add a line, delete a line that is now wrong, or skip.
- If Sid corrected something a guide already covers, that rule didn't work. Reword it or move it where agents will see it, instead of adding a second copy.
- Create a new topic guide only when no trigger fits, and add its one-line pointer to `AGENTS.md`.
- Match the file: short imperative bullets, nested bullets indented 2 spaces. For values that change, say where to look them up instead of copying them.

## 4. Propose, apply, commit

1. Show a numbered list. For each change: the guide, the action, the exact line as it would read (or the line to delete), and a one-line reason. Then list the inbox notes you would drop, each with a reason.
2. Stop and wait for Sid. Apply only what he approves, including his wording edits, with small Edit calls. Never rewrite a whole file.
3. Delete the inbox notes he has decided on, whether approved or dropped.
4. Check that `AGENTS.md` is under about 120 lines, name any guide over about 200 lines as a split candidate, and make sure no credential-shaped strings went in.
5. From `/Users/siddharthks/Developer/0xsiddharthks/mysten`, commit only the files you changed and push: `git add -- <files>`, `git commit -m "[agent-context] <what was learned>" -- <files>`, `git push`. Never bypass signing or hooks. If the push is rejected, stop and tell Sid.
6. Report what changed, what was dropped, and how many inbox notes remain.
