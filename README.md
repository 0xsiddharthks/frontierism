# frontierism

Building the new Frontier.

- [`skills/`](skills/README.md): my agent skills for Claude Code and Codex.
- [`mods/`](mods/README.md): my Claude Code mods. `/prs` shows my open PR stacks; `/files` browses repository files, Git changes, and session activity, with previews and selection for the prompt.
- `setup/` contains the Mac installers and configuration. [New Mac guide](setup/provision/README.md#new-machine) · [Dotfiles](setup/dotfiles/README.md) · [Preferences](setup/preferences/README.md)

## Install

Each area has its own installer. Run these commands from the repository root.

| Installer | What it does |
| --- | --- |
| `./setup/provision/install.sh` | Install apps and command-line tools. |
| `./setup/dotfiles/install.sh` | Add missing configuration and report existing files that differ. |
| `./skills/install.sh` | Link skills into Claude Code and Codex. |
| `./mods/install.sh` | Link mods into Claude Code. |
| `./setup/preferences/install.sh` | Apply macOS and app defaults. |

All five accept `--check` to report differences without applying changes. The
[new Mac guide](setup/provision/README.md#new-machine) also covers private files
and manually installed apps.

`./setup/install.sh` runs the installers in order.

```sh
./setup/install.sh               # link skills and mods
./setup/install.sh --check       # check skills and mods
./setup/install.sh --all         # provision → dotfiles → skills → mods → preferences
./setup/install.sh --all --check # check all five areas, even if some report differences
```

`--all` stops if a step fails, including when it reports configuration drift or
unlisted packages. Resolve the reported differences with that area's installer,
then rerun it. Use `./setup/dotfiles/install.sh --push` to replace starter or
changed configuration and keep backups. Pass `--push` and `--pull` directly to
the individual installers that support them.

Run `python3 -m unittest discover -s setup/tests` to test the installer with
temporary home directories.
