# Dotfiles

My terminal, shell, editor and agent config for macOS.

| Here                           | Goes to                                                      |
| ------------------------------ | ------------------------------------------------------------ |
| `claude/cw`                    | `~/.local/bin/cw`                                            |
| `claude/settings.json`         | `~/.claude/settings.json`                                    |
| `claude/statusline-command.sh` | `~/.claude/statusline-command.sh`                            |
| `cursor/settings.json`        | `~/Library/Application Support/Cursor/User/settings.json`   |
| `cursor/keybindings.json`     | `~/Library/Application Support/Cursor/User/keybindings.json` |
| `cursor/extensions.txt`       | installed with `cursor --install-extension`                 |
| `cursor/preferences.json`    | selected Cursor app preferences, merged into its local storage |
| `ghostty/config`               | `~/Library/Application Support/com.mitchellh.ghostty/config` |
| `herdr/config.toml`            | `~/.config/herdr/config.toml`                                |
| `herdr-app/`                  | personal settings, keys, themes, layout and mods in `~/.config/herdr-app/` |
| `rex/rex`                     | `~/.local/bin/rex`                                          |
| `rex/init.lua`                | `~/.config/rex/init.lua`                                    |
| `rex/preferences.json`        | selected Rex Mac settings, applied with `defaults`          |
| `zsh/zprofile`                 | `~/.zprofile`                                                |
| `zsh/zshrc`                    | `~/.zshrc`                                                   |

## Use

From the repo root:

```sh
./dotfiles/install.sh          # add what is missing; report files that differ, without overwriting
./dotfiles/install.sh --check  # only report
./dotfiles/install.sh --pull   # copy home's versions here, to review and commit
./dotfiles/install.sh --push   # overwrite home's copies from here, keeping a .bak-<time> of each
```

The files are copied, not linked, because the apps rewrite their config, and installers add lines to the zsh files. After changing a setting in an app, run `--pull` and commit. After editing a file here, run `--push`.

To bring another laptop up to date, pull what it changed first, so git can merge the two:

```sh
./dotfiles/install.sh --pull   # copies this laptop's changes here; review and commit them
git pull --rebase
./dotfiles/install.sh --push
```

This repo is public, so `--pull` refuses a file that looks like it holds a credential.

## Herdr

The [desktop app configuration](herdr-app/README.md) migrates the TUI preferences:
`Cmd+1`–`Cmd+9` selects spaces; numeric tab switching is disabled; Tokyo Night
follows macOS light/dark appearance; sounds are off; agents show two lines in priority order; the tab strip
hides at one tab. A persistent header keeps the current task, folder and branch,
Files, Changes, Cursor and the new-terminal/agent menu accessible. Terminal text uses
JetBrains Mono at a base 16 px with 120% app zoom; telemetry is off. Personal layout
and mod copies survive app updates. The [preferences step](../preferences/README.md)
enables macOS's automatic day/night appearance on new machines.
The older TUI keeps its prefix bindings and follows its host terminal's appearance;
its light/dark theme pair is enabled too.

The installer checks and selects the personal layout while Herdr is running, or
saves the selection for its first launch on a new machine. `--check` verifies the
managed files and selection without opening Herdr. To apply only Herdr, run
`./dotfiles/herdr-app/setup.py --push` from the repo root. Its [migration notes](herdr-app/README.md#migrated-preferences)
record the old options that have no direct desktop equivalent.

## Editors and Rust

Cursor is the only GUI code editor installed by [provision](../provision/README.md)
and configured here. Vim is the shell's preferred editor (`EDITOR` and `VISUAL` use `vim`).
The [preferences installer](../preferences/README.md) sets Git's global
`core.editor` to `vim` for commit messages, amend and interactive rebase.
Vim comes with macOS, so no extra package is needed. Cursor is the default for
code/text files in macOS and for opening files and repositories from Codex and Herdr.
It uses JetBrains Mono at 16 px, automatic line height and its built-in Default
Light Modern and Default Dark Modern themes, following the system appearance.

The Cursor files capture the current editor settings, keyboard shortcuts and
installed extension IDs. Extensions use Cursor's installer, including
its Anysphere Python and remote-development extensions.
The current Cursor profile has no custom snippets, tasks or named profiles.

`cursor/preferences.json` also captures a selected set of app preferences:
Cursor Tab is disabled, and the current privacy, agent, model, notification and
sidebar-size preferences and disabled-extension list are saved.
The helper reads and merges only explicitly named fields; it never exports the
whole database, sign-ins, team/account identifiers, chat history, MCP connections
or crash-reporting identifiers. Close Cursor before applying changed app
preferences; `--pull` and `--check` work while it is open. Existing local state is
backed up beside its database before a change. Cursor's storage format is internal,
so app upgrades may require updating this helper. Model availability still follows
the signed-in account. To sync just these preferences, run
`python3 dotfiles/cursor/preferences.py --pull`, `--push` or `--check` from the repo root.

The Cursor extension list includes rust-analyzer and Even Better TOML. Provision
installs rustup's `rust-src`, `rustfmt` and `clippy` components for analysis,
formatting and linting.

Cursor excludes directories named `worktrees` or `.worktrees` at any depth,
including `.claude/worktrees/` and `.codex/worktrees/`, so opening a parent repo
doesn't scan the nested checkouts. Open a particular worktree as its own project
when working in it. Cursor excludes these folders from its explorer, recursive
watcher and Git repository discovery; searches inherit the explorer exclusions.
It also excludes Cargo's `target` build output from scanning/watching. If adding
another worktree container name, update Cursor's settings here. Project settings
that override these lists should keep these patterns.

## Rex

Install [Rex Beta](https://blob.superlogical.com/download/rex-app/preview/latest.dmg)
manually into `/Applications` first. The installer sets up its CLI, Zsh
completion, terminal support, Claude Code and Codex skills and hooks, and the
[configuration and workflow](rex/README.md). Rex is deliberately absent from the
Brewfile until there is a supported cask.

`--check` checks the generated pieces too. `--push` backs up and applies the
selected Mac preferences; `--pull` reads only those preferences, never
the app's full preferences or its list of hosts. Rex's generated skill stays
managed by the installed app rather than being copied into `skills/`.

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

## zsh

`zsh/zshrc` loads Oh My Zsh with the plugins it names, then zsh-autosuggestions and zsh-syntax-highlighting. All three are installed by [`../provision/install.sh`](../provision/README.md), along with the commands the plugins complete. `zsh/zprofile` runs `brew shellenv`, which is what lets zsh find the completions Homebrew installs.

Tokens and work details go in `~/.zshrc.private`, which `~/.zshrc` reads if it is there. That file isn't in this repo, so it is carried to a new Mac by hand. When something adds a credential to `~/.zshrc`, `--pull` refuses the file until the line is moved there.

## New machine

Run these steps from the repo root:

1. Install the apps and tools with [`./provision/install.sh`](../provision/README.md#new-machine), then run `./dotfiles/install.sh --push`. It is `--push` because some installers have already written a config of their own by then, such as the `~/.zshrc` that Oh My Zsh starts with.
2. Bring `~/.zshrc.private` over from the old Mac, and open a new terminal.
3. Run `./install.sh` to link the skills and mods.
4. If using the older Herdr TUI, run `herdr integration install claude` and
   `herdr integration install codex`. It manages its own hook scripts, so they
   aren't kept here. The desktop app uses herdr-core and the agents' OSC 7501
   status reports; these TUI integrations do not configure the desktop app.
5. Run the installer in my private guides repo for the other hook the Claude settings name.
6. Run `./preferences/install.sh` to enable macOS's automatic day/night appearance, make Cursor the default for code/text files and app integrations, configure Codex's `.codex-root` discovery, and select Vim for Git editing. See [preferences](../preferences/README.md) for checking and backups.

Not kept here: git config, `~/.zshenv`, which rustup's installer writes, anything that holds credentials, and Codex's full `config.toml`, which is mostly per-machine state. The preferences step applies only selected portable Codex settings, including `.codex-root` discovery and Cursor defaults. Rex generates its Codex hook in `~/.codex/hooks.json` without copying that file here. The Claude settings name their hook and status line scripts by absolute path under `/Users/siddharthks`, and so do a few `PATH` lines in the zsh files.
