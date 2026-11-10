# Mods

My Claude Code mods. A mod is a plugin whose code runs inside Claude Code, so it can add commands and draw panes. A skill is only instructions.

| Mod        | What it does                                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------------------------ |
| `pr-stack` | `/prs`: a pane of my open PRs in the current repo as stacks, with CI and review state, refreshed while it is open. |
| [`files`](files/README.md) | `/files`: a searchable file tree with All files, Git changes, and This session views, content/diff previews, and selected paths added to the draft prompt. |

`/prs` reads the PRs with `gh`, so `gh` has to be signed in.
`/files` needs Git and Python 3.9 or later, and runs in a Git working tree.

## Install

From the repo root:

```sh
./mods/install.sh          # link mods into ~/.claude/skills
./mods/install.sh --check  # only report
claude plugin list    # pr-stack@skills-dir and files@skills-dir should be enabled
```

Claude Code loads a plugin folder it finds in `~/.claude/skills` as `<name>@skills-dir`. It needs Claude Code 2.1.287 or later, and Codex can't run a mod. A session that is already open picks up a change after `/reload-plugins`.

Only folders containing `.claude-plugin/plugin.json` are linked; unfinished
folders are ignored. The installer removes broken links belonging to this
checkout's mods, preserves real files and unrelated broken links, and reports
skill/mod name conflicts. `./setup/install.sh` runs both the skills and mods
installers.

## Working on one

```sh
claude plugin validate mods/pr-stack     # what Claude Code reads from the code
(cd mods/pr-stack && claude plugin test) # its tests
claude --plugin-dir mods/pr-stack        # a session that reloads it as you edit
```

## Adding one

Put the plugin folder (`.claude-plugin/plugin.json` and `hooks/`) in `<name>/` here and run `./mods/install.sh` from the repo root. Gitignore the `.claude-plugin/types/` and `tsconfig.json` that Claude Code writes there.
