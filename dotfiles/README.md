# Dotfiles

My terminal, editor and agent config for macOS.

| Here                           | Goes to                                                      |
| ------------------------------ | ------------------------------------------------------------ |
| `claude/cw`                    | `~/.local/bin/cw`                                            |
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

The files are copied, not linked, because the apps rewrite their config. After changing a setting in an app, run `--pull` and commit. After editing a file here, run `--push`.

To bring another laptop up to date, pull what it changed first, so git can merge the two:

```sh
./install.sh --pull   # copies this laptop's changes here; review and commit them
git pull --rebase
./install.sh --push
```

This repo is public, so `--pull` refuses a file that looks like it holds a credential.

## cw

`cw` starts Claude Code in its own git worktree, so sessions running side by side don't share files.

```sh
cw                # new worktree and branch named wt-<date>-<time>
cw fix-login      # new worktree, branch and session named fix-login, or back into it if it exists
cw fix-login -c   # anything after the name is passed to claude
```

Run it anywhere inside a repo. Worktrees go under `.claude/worktrees/` in the main checkout, and a new one branches from the current `HEAD`. A name you give is also the session's name, which is what the prompt bar, the terminal title and Remote Control show.

I use it instead of `claude -w`. A `-w` session checks every shell command and refuses the ones it can't prove keep git inside the worktree. That catches harmless commands such as `bash --version`, and the check can't be turned off. A worktree made with git doesn't get those checks. In exchange, nothing stops the session from touching the main checkout, and nothing is cleaned up on exit:

```sh
git worktree remove .claude/worktrees/fix-login
git branch -d fix-login
```

`cw` is installed to `~/.local/bin`, which has to be on `PATH`. Claude Code's installer puts `claude` there too.

## Claude settings

`claude/settings.json` is my Claude Code config for every repo. A repo's own settings go in its tracked `.claude/settings.json`. Both are in git, so they reach every laptop.

I keep nothing in `.claude/settings.local.json`. Git ignores that file, so what it holds stays on one machine. Claude Code writes it when I pick "don't ask again" on a permission prompt. When one turns up, I move what it holds into the repo's `.claude/settings.json` and delete it.

`"tui": "fullscreen"` turns on the fullscreen renderer, which draws on the terminal's alternate screen and doesn't flicker. Claude Code picks its renderer at startup, so the setting applies from the next session. `/tui default` switches a running session back and saves that to `~/.claude/settings.json`, so run `--pull` afterwards.

## New machine

1. Install the apps and tools with [`../provision/install.sh`](../provision/README.md#new-machine), then run `./install.sh --push` here.
2. Run `../install.sh` to link the skills.
3. Run `herdr integration install claude` and `herdr integration install codex`. herdr manages its own hook scripts, so they aren't kept here.
4. Run the installer in my private guides repo for the other hook the Claude settings name.

Not kept here: shell and git config, anything that holds credentials, and Codex's `config.toml`, which is mostly per-machine state. The Claude settings name their hook and status line scripts by absolute path under `/Users/siddharthks`.
