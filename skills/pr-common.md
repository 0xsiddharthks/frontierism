# Shared steps for the PR skills

`pr-rebase`, `pr-self-review`, `pr-address-feedback` and `pr-groom` all follow this file, and `pr-peer-review` follows sections 1 and 2. Skill files live in `/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/<name>/SKILL.md`, and the guides these skills name (`AGENTS.md`, `git-and-prs.md`, ...) in `/Users/siddharthks/Developer/0xsiddharthks/mysten/agent-context/memory/`.

## 1. Plan the run

- Take the arguments from the invocation. If the tool didn't substitute them into the skill, take them from Sid's message.
- PR references: `1167`, `#1167`, `owner/repo#1167`, or a PR URL. Bare numbers belong to the repo of the current working directory. With no reference, use the PR for the current branch (`gh pr view`); if there isn't one, ask.
- Any `pr-*` skill named in the arguments or the message (`/pr-groom`, `$pr-groom`, `pr-groom`) is chained onto the same PRs. Read its `SKILL.md` and follow it; don't wait for it to be invoked. Run each skill once per PR, even if the tool also loaded it.
- The rest of the arguments is guidance from Sid for this run, e.g. "focus on the retry path".
- Order: `pr-rebase` runs first, over all the PRs, so the others work on the rebased code. Then go PR by PR. For PRs that form a stack, go bottom-up; otherwise go in the order given. Within a PR, run `pr-address-feedback`, then `pr-self-review`, then `pr-groom`, whatever order they were typed in, so the body describes the final diff.
- If `pr-rebase` is chained and a later skill pushes to a PR with PRs stacked on it, finish by rebasing those PRs onto it with `pr-rebase`.
- With several independent PRs, you may give each PR to its own subagent if your tool has them. Keep a stack in one sequential run.

## 2. Set up each PR

1. `gh pr view <ref> --json number,url,title,body,author,state,isDraft,baseRefName,headRefName,headRefOid,commits,files`
2. If it's merged or closed, skip it and say so. If `author` isn't Sid (`gh api user --jq .login`), change nothing: no commits, pushes or body edits. Report what you would change instead.
3. Read `git-and-prs.md`, the repo's own `CLAUDE.md` and `AGENTS.md`, and every topic guide in `AGENTS.md` whose area the PR touches.
4. If the base isn't the default branch, it's stacked: find the parent with `gh pr list --head <base>`, and PRs stacked on this one with `gh pr list --base <head>`.
5. For skills that read or change code, get a checkout of the PR head:
   - If the current checkout is on the head branch and matches `headRefOid` (or is ahead of it), use it.
   - Otherwise `git fetch origin`, then `git worktree add --detach <path> origin/<head>`. Put `<path>` under the main checkout's `.claude/worktrees/` (the parent directory of `git rev-parse --path-format=absolute --git-common-dir`), named `pr-<number>`, with a suffix if that exists. Never edit a checkout another session is using, even when it has the branch.
   - For a PR in another repo, find the repo under `~/Developer` and create the worktree there. If your tool refuses git commands outside the current checkout, stop and ask Sid.
6. The PR's diff is `git diff origin/<base>...HEAD` (three dots), or `gh pr diff <n>` without a checkout.

## 3. Commit and push

- Add new commits once a PR has review comments or PRs stacked on it, so reviewers see what changed; otherwise amending a leaf is fine. A force-push doesn't dismiss approvals in MystenLabs repos. Rebase only when Sid asks (running `pr-rebase` is asking).
- Use the PR title's `[tag]` in commit subjects, and say what changed, not "address review".
- Before committing, run the repo's pre-push checks for the touched code (for hashi, "Before pushing" in `hashi-development.md`). Stage only the files you changed; never `git add -A`.
- Push with `git push origin HEAD:refs/heads/<head>`, adding `--force-with-lease=refs/heads/<head>:<old-head>` after an amend. If it's rejected because the branch moved, stop and tell Sid.
- If PRs are stacked on this one, list them in the report. Don't rebase them unless Sid asks.
- Never reply to, react to or resolve review comments, request reviews, or mark the PR ready. `pr-groom`'s edits to Sid's own PR title and body, and `pr-rebase`'s base changes and `Stacked on` line updates, are the only GitHub writes besides pushes.

## 4. Report

One short section per PR, after all skills have run on it:

- The PR link, and the worktree path if you made one.
- What you changed, with short commit SHAs.
- What needs Sid's decision, each with the trade-off in a line or two.
- What you verified and how (commands and results), and what you didn't verify.
