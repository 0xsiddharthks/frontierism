# Skills

My agent skills for Claude Code and Codex.

| Skill                                                            | What it does                                                                                       |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `learn`                                                          | `/learn`: saves lessons from a session into my agent guides, after I approve each change.          |
| `audit-memory`                                                   | `/audit-memory`: re-checks those guides against current code, fills gaps, and reports what it saw. |
| `pr-self-review`, `pr-groom`, `pr-address-feedback`, `pr-rebase` | For my own PRs. They chain, and share `pr-common.md`.                                              |
| `pr-peer-review`                                                 | For colleagues' PRs: keeps only real issues, and posts the review when I say so.                   |
| `pr-stack`                                                       | `/prs`: a Claude Code mod, not a skill. A pane of my open PRs as stacks, with CI and review state. |
| `socratic-learning`                                              | Socratic tutoring and debate practice.                                                             |
| `xurl`                                                           | Read-only X research: in-app browser by default, xurl for explicit API requests.                   |

## Install

Run `install.sh` from the repo root:

```sh
./install.sh          # link every skill into ~/.claude/skills and ~/.agents/skills
./install.sh --check  # only report
```

Re-run it after adding a skill or moving this repo. `~/.agents/skills` is Codex's user skills directory.

The skills are written for my own setup. They refer to each other and to my agent guides, which live in a private repo, by absolute path, because agents load them through symlinks.

## Adding one

- **Skill:** create `<name>/SKILL.md` in this folder, then run `./install.sh`. For a skill that should run only when invoked, set `disable-model-invocation: true` for Claude and add `agents/openai.yaml` with `policy: allow_implicit_invocation: false` for Codex. Codex doesn't substitute `$ARGUMENTS`, so say where to find the arguments when it's left as is.
- **Mod:** put the plugin folder (`.claude-plugin/plugin.json` and `hooks/`) in `<name>/` here and run `./install.sh`; Claude Code loads it from `~/.claude/skills`. Gitignore the `.claude-plugin/types/` and `tsconfig.json` it writes there.
