# Dotfiles

My terminal, editor and agent config for macOS.

| Here                           | Goes to                                                      |
| ------------------------------ | ------------------------------------------------------------ |
| `claude/settings.json`         | `~/.claude/settings.json`                                    |
| `claude/statusline-command.sh` | `~/.claude/statusline-command.sh`                            |
| `ghostty/config`               | `~/Library/Application Support/com.mitchellh.ghostty/config` |
| `herdr/config.toml`            | `~/.config/herdr/config.toml`                                |
| `vscode/settings.json`         | `~/Library/Application Support/Code/User/settings.json`      |
| `vscode/extensions.txt`        | installed with `code --install-extension`                    |
| `zed/settings.json`            | `~/.config/zed/settings.json`                                |

## Use

```sh
./install.sh          # add what is missing; report files that differ, without overwriting
./install.sh --check  # only report
./install.sh --pull   # copy home's versions here, to review and commit
./install.sh --push   # overwrite home's copies from here, keeping a .bak-<time> of each
```

The files are copied, not linked, because the apps rewrite them. After changing a setting in an app, run `--pull` and commit. After editing a file here, run `--push`.

This repo is public, so `--pull` refuses a file that looks like it holds a credential.

## New machine

1. Install the apps, then run `./install.sh --push` here.
2. Run `../install.sh` to link the skills.
3. Run `herdr integration install claude` and `herdr integration install codex`. herdr manages its own hook scripts, so they aren't kept here.
4. Run the installer in my private guides repo for the other hook the Claude settings name.

Not kept here: shell and git config, anything that holds credentials, and Codex's `config.toml`, which is mostly per-machine state. The Claude settings name their hook and status line scripts by absolute path under `/Users/siddharthks`.
