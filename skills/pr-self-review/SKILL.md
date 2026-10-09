---
name: pr-self-review
description: Review one of Sid's own PRs before it goes to his manager or tech lead. Re-derives the problem and challenges the approach from first principles, proves correctness and completeness, checks the code matches the crate's patterns, trims comments, fixes what's clear-cut and reports the rest. Takes PR numbers or URLs, and chains with pr-address-feedback and pr-groom. Use only when Sid runs /pr-self-review or explicitly asks for it.
argument-hint: "[pr ...] [pr-* skills to chain] [notes]"
disable-model-invocation: true
---

# PR self-review

Arguments: `$ARGUMENTS`

First read `/Users/siddharthks/Developer/0xsiddharthks/frontierism/skills/pr-common.md` and follow it for arguments, chaining, checkout, commits and the report.

The goal: the reviewer finds nothing Sid should have caught. Review as a skeptical senior engineer who didn't write this PR. An earlier session probably wrote much of it, so treat its code, comments and PR body as claims to check, not as context.

## 1. Understand the problem

- Read the title, body, linked issues, commit messages, and the whole diff against the base.
- Read the code around every change, including callers and callees, until you know why it was shaped that way before the PR.
- Write down, in two sentences, the problem and the constraints any fix must meet. If you can't, find out before going further.

## 2. Challenge the approach

Sketch how you would solve the problem from scratch, then compare it with the PR:

- Does it fix the root cause or a symptom?
- Is it the simplest correct design? Look for parts it doesn't need: traits, generics, config knobs or feature flags with one use, caches, background tasks, retries, new dependencies, new persisted state.
- Find the closest existing code that solves a similar problem. Does the PR follow that pattern, or have a real reason not to?
- Is it one concern? Unrelated refactors, renames and churn should go.
- Does it hold against the architecture guide for this area: compatibility, on-chain and storage formats, mixed versions during a rollout, deployed state?

If a clearly better approach exists, don't rewrite the PR. Make it the top item in the report with both designs and the trade-off, and finish the remaining steps on the current design.

## 3. Prove it's correct

For each behavior the PR adds or changes, state the invariants, then try to break them:

- Error paths: every `?`, `unwrap`/`expect`, `.ok()`, `let _ =`, default-on-error, and log-and-continue. Errors propagate or fail closed; nothing is swallowed or downgraded.
- Restarts and partial failure: what if the process dies between any two steps, or a step runs twice? Retries cover only errors known to be transient.
- Concurrency and ordering: races, locks held across `.await`, cancellation of dropped futures and `select!` branches, reordered messages, stale reads.
- Time: a timeout is one deadline set by the caller and checked right before any side effect.
- Boundaries: empty, zero, one, max, overflow, rounding, off-by-one, unit mix-ups (sats and BTC, ms and s).
- Trust: data from the chain, network, config or users is validated before use.

Follow every changed function, type, field and config key to all its uses across the repo, not just the diff. For each suspected bug, find the concrete trigger and confirm it in code or with a test. Drop suspicions you can't back.

## 4. Check nothing is missing

- Callers, sibling code paths and parallel implementations are updated too. The same bug often sits next door.
- Tests cover each changed behavior, failure paths included, and would fail without the change.
- Generated code is regenerated. Config, docs, runbooks, CLI, metrics and alerts are updated where the change reaches them. Note counterpart changes that belong in another repo (sui-operations, ts-sdks, the frontend).
- No leftovers: debug output, stray TODOs, commented-out code, code the change made dead, unused dependencies.
- The PR body's claims match the diff. Note mismatches; `pr-groom` fixes the body.

## 5. Match the codebase

For each new piece of code, compare it with 2-3 similar places in the same crate or package: error types and handling, existing helpers, naming, module layout, logging and metrics style, test structure and helpers. Prefer the crate's way over a generic best practice, and write idiomatic code for the language.

## 6. Trim comments

Apply the Comments rules in `AGENTS.md` to every comment, doc comment and prose line the PR adds or changes:

- Look at the surrounding file's comments first and match their density and style.
- Delete comments that restate the code, mention the task, PR or review, or describe what wasn't done.
- Keep only non-obvious whys, 1-2 lines each, stated once on the most canonical item.
- Leave comments the PR didn't touch alone.

## 7. Fix, verify, report

- For a non-trivial PR, if your tool can run a subagent, give one with fresh context only your problem statement from step 1 and the diff, and ask it for correctness bugs and simpler designs. Its findings are leads: verify each one yourself.
- Fix the clear-cut issues: bugs with a confirmed trigger, missing tests, consistency and idiom fixes, comment trims, leftovers. Stay inside the PR's scope.
- Leave for Sid: approach changes, behavior changes beyond the PR's intent, and judgment calls.
- Run the checks, commit and push as in `pr-common.md`.
- Report as in `pr-common.md`, starting with a one-line verdict on the approach.
