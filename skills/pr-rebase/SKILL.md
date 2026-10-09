---
name: pr-rebase
description: Rebase one of Sid's PRs, or the whole stack it belongs to, onto the latest upstream default branch. Skips PRs in the stack that already merged, resolves conflicts against the new base, checks every rebased head, force-pushes with leases and retargets bases. With `only`, rebases just the named PR onto its parent's current head and leaves the PRs above it alone. Takes PR numbers or URLs, and chains with the other pr-* skills. Use only when Sid runs /pr-rebase or explicitly asks for it.
argument-hint: "[pr ...] [only] [pr-* skills to chain] [notes]"
disable-model-invocation: true
---

# PR rebase

Arguments: `$ARGUMENTS`

First read `/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/pr-common.md` and follow it for arguments, chaining, setup and the report. Running this skill is Sid asking to rebase and force-push the PRs it rewrites. Then read "Stacked PRs and rebases" in `git-and-prs.md`; this skill is how to apply it.

## 1. Pick the mode and map the stack

- **Stack (default):** rebase every open PR in the stack of each named PR, from the lowest open PR up through all open PRs above it, onto the latest default branch. A PR with no stack is a stack of one, and a named PR that merged still names the stack above it.
- **Only:** when the arguments say `only`, or Sid asks for just that PR, rebase only the named PRs, each onto its parent's current head. That's the parent PR's branch as it is now, or the default branch if the base is the default branch or the parent merged. Leave the PRs above it untouched.

Map the stack from GitHub, not from local refs:

1. `git fetch origin` (or the remote for the PR's repo), and get the default branch from `gh repo view --json defaultBranchRef`.
2. Down: follow `baseRefName` with `gh pr list --head <base> --state all --json number,state,author,baseRefName,headRefName,headRefOid` until you reach the default branch, taking the open or merged PR for each branch. Keep going below a parent that merged.
3. A PR based on the default branch may have been stacked on a PR that merged, with GitHub retargeting it since. Check its base changes with the query below, and a `> Stacked on #<n>.` first line in its body.
4. Up: `gh pr list --base <head> --state open` from each PR, recursively. A stack can branch; treat it as a tree.
5. Every PR you will rewrite must be Sid's, open, and have `origin/<head>` equal to `headRefOid`. If a PR inside the stack is closed without merging, or a head doesn't match, stop and tell Sid. Don't rebase someone else's PR stacked on one of Sid's; list it, since its base changes under it.

Record each branch's head SHA before changing anything. These are the old heads for step 2 and the push leases.

The history query returns a PR's base changes and every past head from its force pushes:

```sh
gh api graphql -F owner=<owner> -F name=<repo> -F number=<n> \
  -F query=@/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/pr-rebase/pr-history.graphql
```

## 2. Find each PR's own commits

A PR's own commits are `<boundary>..<old-head>`, where the boundary is the commit it was built on:

- No parent PR, open or merged: `git merge-base origin/<default> <old-head>`.
- A parent, open or merged: try the parent's recorded head (its final `headRefOid` if merged), then each `afterCommit` and `beforeCommit` from the parent's force pushes, newest first. Use the first one that is an ancestor of the old head (`git merge-base --is-ancestor`). If none is, the parent moved on after this PR branched: use the merge base of the old head with each candidate, taking the one closest to the old head.

Check the range before replaying it. `git log --oneline <boundary>..<old-head>` must hold only this PR's commits and none of its parent's (compare with `gh pr view <parent> --json commits`). Merge commits in the range, such as from GitHub's "Update branch", pull base commits into it; step 3 replays only the PR's own commits then. If the range is ambiguous, stop and show Sid the candidates.

## 3. Rebase bottom-up

Use one detached worktree for the whole run, set up as in `pr-common.md` and named after the lowest PR. Rebase parents before children:

```sh
git -c merge.conflictStyle=zdiff3 rebase --no-update-refs --no-autosquash \
  --onto <new-base> <boundary> <old-head>
```

- `<new-base>` is `origin/<default>` for the lowest open PR, the parent's new head for each PR above it, and in only mode the parent's current head (its new head if this run rebased it).
- `--no-update-refs` and `--no-autosquash` override local git config that would move other branches or fold `fixup!` commits. Rebasing a SHA leaves HEAD detached, so no checked-out branch moves.
- If `<new-base>` is already `<boundary>`, the PR is up to date; keep its head.
- If the range has merge commits, replaying it would re-apply the base commits they brought in. Instead run `git switch --detach <new-base>`, then `git cherry-pick` the commits from `git rev-list --reverse --first-parent --no-merges <boundary>..<old-head>`.
- Record `git rev-parse HEAD` as the PR's new head.
- Rebased commits are re-signed. If signing fails, run `git rebase --abort` and stop.

Resolve conflicts from both sides' intent:

- Know what the PR's commit does (its diff, message and the PR body) and what upstream changed in those paths (`git log -p <boundary>..<new-base> -- <path>`, and the PRs behind it). Read the design doc for the flow.
- During a rebase, "ours" is the new base and "theirs" is the PR's commit. Don't take one side wholesale unless the other is truly superseded.
- Re-apply the PR's change to the new structure. If upstream moved or renamed the code, make the edit in the new place. If upstream deleted it, don't bring it back, tests included.
- Regenerate generated files as in `git-and-prs.md`. For lock files, take the new base's version and let the build update it.
- If upstream's change makes the PR's approach wrong or redundant, run `git rebase --abort` and ask Sid.
- Check unresolved review threads on the conflicting code (`pr-address-feedback`'s query) so the resolution doesn't undo a pending fix. Addressing them is that skill's job.

## 4. Verify each rebased head

Do this for each PR before rebasing its children onto it:

1. `git range-diff <boundary>..<old-head> <new-base>..<new-head>`. Only commits you resolved by hand may differ, and base commits a merge brought in appear only on the old side. Explain any other difference, and confirm every commit the rebase dropped really landed upstream.
2. `git diff --stat <new-base>...<new-head>` names the files the PR changed before, minus any that upstream already landed.
3. Build the head: `cargo check --workspace --all-features --all-targets` in hashi, or the repo's equivalent.
4. If you resolved conflicts, or upstream changed the crates the PR touches (`git diff --stat <boundary> <new-base> -- <paths>`), also run the repo's pre-push checks on those crates.
5. If a check fails, run it on `<new-base>` as well. A failure there is upstream's: report it and leave it. A failure only on the head is a semantic conflict: fix it in a new commit on that PR (`[tag] Adapt to <upstream change>`), run the checks again, and use that commit as the new head.

## 5. Push and update the PRs

1. Push every rebased branch in one atomic push, each leased to its recorded old head, so a fetch during the run can't weaken the lease:

   ```sh
   git push --atomic origin \
     --force-with-lease=refs/heads/<branch>:<old-head> <new-head>:refs/heads/<branch> \
     ...
   ```

   If it's rejected, nothing moved: stop and tell Sid.

2. For each PR whose parent merged, run `gh pr edit <n> --base <branch>` with its new parent's branch, or the default branch, unless GitHub already retargeted it. If GitHub refuses because it's a GitHub-managed stack, tell Sid to break the stack in the UI.
3. If the body starts with `> Stacked on #<merged parent>.`, point that line at the new parent, or remove it if the base is now the default branch. Change no other line: fetch the body, edit that line in a temp file, and `gh pr edit <n> --body-file <file>`.
4. Confirm each PR's `headRefOid` and `baseRefName` with `gh pr view`. If the head is stale, switch the base away and back as in `git-and-prs.md`.
5. Sync the primary checkout only as `git-and-prs.md` allows. Don't move other worktrees or local branches; list those still at an old head.

## 6. Report

As in `pr-common.md`, plus for each PR:

- The old and new head SHAs and the new base.
- Commits dropped as already upstream, each conflict and how you resolved it, and any commits you added.
- PRs left on old commits: the ones above in only mode, and other people's PRs stacked on a rewritten branch.
