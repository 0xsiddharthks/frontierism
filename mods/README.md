# Mods

My Claude Code mods. A mod is a plugin whose code runs inside Claude Code, so it can add commands and draw panes. A skill is only instructions.

| Mod        | What it does                                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------------------------ |
| `pr-stack` | `/prs`: a pane of my open PRs in the current repo as stacks, with CI and review state, refreshed while it is open. |

`/prs` reads the PRs with `gh`, so `gh` has to be signed in.

## Install

Run `install.sh` from the repo root:

```sh
./install.sh          # link every mod into ~/.claude/skills
./install.sh --check  # only report
claude plugin list    # pr-stack@skills-dir should be enabled
```

Claude Code loads a plugin folder it finds in `~/.claude/skills` as `<name>@skills-dir`. It needs Claude Code 2.1.287 or later, and Codex can't run a mod. A session that is already open picks up a change after `/reload-plugins`.

## Working on one

```sh
claude plugin validate mods/pr-stack     # what Claude Code reads from the code
(cd mods/pr-stack && claude plugin test) # its tests
claude --plugin-dir mods/pr-stack        # a session that reloads it as you edit
```

## Adding one

Put the plugin folder (`.claude-plugin/plugin.json` and `hooks/`) in `<name>/` here and run `./install.sh`. Gitignore the `.claude-plugin/types/` and `tsconfig.json` that Claude Code writes there.
