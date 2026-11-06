# frontierism

Building the new Frontier.

- [`skills/`](skills/README.md): my agent skills for Claude Code and Codex.
- [`mods/`](mods/README.md): my Claude Code mods. `/prs` shows my open PR stacks; `/files` browses repository files, Git changes, and session activity, with previews and selection for the prompt.
- [`provision/`](provision/README.md): what I install on a new Mac: Homebrew with its formulae and casks, and a few tools from their own installers. Run this first on a new machine.
- [`dotfiles/`](dotfiles/README.md): my terminal, shell, editor and agent config, with an installer for a new machine. It also installs [`cw`](dotfiles/README.md#cw), which starts Claude Code in its own git worktree: `cw [name]`.
- [`preferences/`](preferences/README.md): app defaults to apply afterwards, including Cursor for code/text files and app integrations, Codex's `.codex-root` discovery, and Vim for Git editing. Run `./preferences/install.sh`; `--check` only reports differences.

## Install

Each area owns its installer. Run these from the repository root:

| Installer | What it does |
| --- | --- |
| `./provision/install.sh` | Install apps and command-line tools. |
| `./dotfiles/install.sh` | Add missing configuration; report existing files that differ. |
| `./skills/install.sh` | Link skills into Claude Code and Codex. |
| `./mods/install.sh` | Link mods into Claude Code. |
| `./preferences/install.sh` | Apply macOS and app defaults. |

All five accept `--check` to report differences without applying changes. For a
new Mac, follow the [setup guide](provision/README.md#new-machine), including the
private files and manually installed apps.

The root `install.sh` delegates to these installers:

```sh
./install.sh              # skills and mods, preserving the original behavior
./install.sh --check      # check skills and mods
./install.sh --all        # provision → dotfiles → skills → mods → preferences
./install.sh --all --check # check all five areas, even if some report differences
```

`--all` stops if a step fails, including when it reports configuration drift or
unlisted packages. Resolve the reported differences with that area's installer,
then re-run. It uses the dotfiles installer's normal mode; to replace starter or
changed configuration deliberately, use `./dotfiles/install.sh --push`, which
keeps backups. `--push` and `--pull` belong to the directory installers and are
not accepted at the root.

Installer safety checks use temporary homes:
`python3 -m unittest discover -s tests`.
