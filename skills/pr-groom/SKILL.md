---
name: pr-groom
description: Rewrite the title and description of one of Sid's PRs so a reviewer gets it quickly. A plain Summary of why the PR exists and what it fixes, and a concise Changes list, every line checked against the diff and free of LLM-speak. Takes PR numbers or URLs, and chains with pr-self-review and pr-address-feedback. Use only when Sid runs /pr-groom or explicitly asks for it.
argument-hint: "[pr ...] [pr-* skills to chain] [notes]"
disable-model-invocation: true
---

# PR groom

Arguments: `$ARGUMENTS`

First read `/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/pr-common.md` and follow it for arguments, chaining and the report. This skill needs no checkout unless the diff alone doesn't explain the change.

The format rules are "Titles" and "PR descriptions" in `git-and-prs.md`. This skill is how to apply them.

## 1. Learn what the PR does now

- Read the whole diff (`gh pr diff <n>`), the commit messages, linked issues, and the current title and body.
- Treat the current body as a draft that may be stale or wrong. Every line you keep or write must be true of the diff as it stands.
- Look for a PR template (`.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/`, or the same name in `docs/` or the repo root). If there is one, it replaces the two-section format; keep the writing concise inside it.

## 2. Write the body

- **Summary:** two short sentences, about 50 words, that a reviewer without context can follow. First what is broken or missing today, then what this PR changes. Leave details to the Changes list.
- **Changes:** one line per meaningful change, most important first, at most about five lines of under 15 words each. Name the concrete thing (type, function, flag, config key, file) and what changed about it, not how it works or why. Fold mechanical fallout (regenerated code, forced renames, imports) into one bullet or leave it out; a tests line, if any, is a few words.
- If the body already has this shape and reads plainly, edit it in place: fix wrong or stale lines, add missing changes, and keep Sid's wording.
- For a stacked PR, the first line is `> Stacked on #<parent>.`

## 3. Remove LLM-speak

Read it as Sid telling his tech lead what the PR does. Cut:

- Inflated words: "introduces", "comprehensive", "robust", "seamless", "ensures", "leverages", "enhances", "streamlines", "critical", "various", "in order to".
- Hedging and self-praise: "should help", "significantly improves", "properly handles".
- Structure noise: bold lead-ins, nested bullets, extra headings, emoji, em-dash asides, a closing line that repeats the summary.
- Restating the title, walking through the diff line by line, or repeating a README the PR adds.
- Test plan or evidence sections, unless a reviewer needs something the diff can't show, and then only a line or two.
- Long sentences chained with colons, semicolons, dashes or parentheses. Split them or keep only the first half.
- Explanations of how the code works or why each choice was made. The diff and its comments carry that.
- Measurements beyond the one number that motivates the PR, and rollout notes or caveats unless they gate the merge.

Use short common words, active voice and concrete nouns. If a sentence could appear in any PR, delete it. Then read it aloud: it should sound like Sid typing to a teammate in Slack, not like an essay. If it doesn't, cut until it does.

## 4. Check the title

Apply the Titles rules. Change the title only if it breaks them or no longer describes the diff. Never rename the head branch: that closes the PR.

## 5. Apply

1. Write the body to a file in your scratch or temp directory, then `gh pr edit <n> --body-file <file>`, adding `--title` if it changed. GitHub keeps the old body in the edit history.
2. Confirm it landed as written with `gh pr view <n> --json title,body`.
3. Show the final title and body in the report.
