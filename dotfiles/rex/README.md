# Rex

Rex manages sessions, tabs and panes. Claude Code is the primary agent; Codex
can run in another tab for the same task. Use one Rex session for a task or
worktree, with an agent tab and a shell for commands and tests. The familiar
`claude`, `cw fix-login`, `claude --continue`, and `codex` commands still work.

Use Rex directly for this workflow. Ghostty and herdr remain available for
their existing sessions. There is no automatic herdr attachment inside Rex.
Herdr's Claude hook checks its own environment and does nothing outside herdr.

## Install on a new Mac

1. Run the [provisioner](../../provision/README.md).
2. Download the [preview DMG](https://blob.superlogical.com/download/rex-app/preview/latest.dmg)
   and drag `Rex Beta.app` into `/Applications`. App installation stays manual.
3. Run `./dotfiles/install.sh` from the repository root, then `./install.sh` for
   the shared skills and mods. Existing files that differ are reported; review
   them before using `./dotfiles/install.sh --push`.
4. Open Rex and start a fresh terminal. In Codex CLI, use `/hooks` to approve
   Rex's session-start hook if prompted. Claude Code runs it in trusted folders.
5. Run `./dotfiles/install.sh --check` to check the files and generated setup.

The dotfile installer handles:

- A `rex` launcher in `~/.local/bin`, usable from Ghostty and agents too. It
  executes the app's bundled CLI; app updates update the CLI automatically.
  Inside Rex, `REX_BIN_DIR` takes precedence so commands use that server's CLI.
- `~/.config/rex/init.lua`, with the shortcuts and agent actions below.
- JetBrainsMono Nerd Font Mono at 18 pt, 8% extra line height, and vertical tabs.
  Left Option sends Alt; right Option still composes characters. Selection
  requires an explicit copy, and program activity alerts are silent, matching
  the Ghostty and herdr preferences. Only these selected preferences are synced.
  Reopen Rex after changing them.
- App control through **Server → Remote Control**, so agents can select a
  session or otherwise operate the Rex app. This is enabled in the preset as
  requested; it lets connected Rex clients perform app actions.
- Zsh completion in `~/.local/share/zsh/site-functions/_rex`, loaded before
  Oh My Zsh initializes completions.
- Rex's own skills and session-start hooks for Claude Code and Codex, using
  `rex skill setup --agent claude --agent codex`. Its generated skill reads
  guidance from the installed version, so it is not vendored in this repo.
- `xterm-rex` terminfo and the SSH fallback using `rex terminfo setup`. Rex adds
  an Include to `~/.ssh/config`; existing SSH settings stay in place. Remote
  hosts without Rex's terminal description receive `xterm-256color`.

The setup can be rerun after a Rex update. It never restarts the server.
`--check` only reads. `--pull` copies the config and selected Mac
preferences back, while leaving generated completions and agent files alone.
`--push` retains backups when it overwrites your config or selected preferences.
The Brewfile deliberately has no Rex entry yet.

## Everyday use

Create a session in Rex, open the repository in its terminal, and start Claude:

```sh
cd ~/Developer/0xsiddharthks/frontierism
claude
```

For a separate Claude worktree, run `cw fix-login` instead. That keeps its
existing branch, worktree and Claude session naming behavior. Rex does not
create or clean up Git worktrees. Give independent editing tasks their own
worktrees and Rex sessions.

Open a shell beside the agent with Cmd+D, or below it with Cmd+Shift+D. New
shells use the source terminal's working directory. Ask the agent to open tests,
logs or a diff in another pane; its Rex skill supplies the relevant commands.

Ctrl+Cmd+C opens a new Claude Code tab; Ctrl+Cmd+X opens Codex. Both use the
focused program's actual directory, including a worktree entered by `cw`, and
load the normal interactive Zsh environment. They also appear in the command
palette as **Claude Code in Current Directory** and **Codex in Current Directory**.
These actions start a fresh agent conversation. Use `claude --continue` or the
agent's own resume command from a shell when continuing a previous conversation.
Tabs retain their output after the agent exits.

| Shortcut | Action |
| --- | --- |
| Cmd+T / Cmd+W | New tab / close the focused pane, tab or window |
| Cmd+1…9 | Select tab |
| Cmd+Shift+[ / ] | Previous / next tab |
| Cmd+D / Cmd+Shift+D | Split right / below |
| Cmd+Option+arrows | Focus a pane |
| Cmd+Shift+Return | Zoom the focused pane / restore layout |
| Cmd+Shift+P | Command palette |
| Cmd+F | Find terminal text |
| Cmd+Up / Down | Previous / next shell prompt |
| Ctrl+Cmd+S | Switch Rex session |
| Ctrl+Cmd+C / Ctrl+Cmd+X | New Claude Code / Codex tab in the current directory |

Shell and agent shortcuts such as Ctrl+C, Ctrl+D, Ctrl+R and Shift+Return
continue to reach the terminal. There is no multiplexer prefix to learn.

The preset enables **Server → Remote Control** for agents to select a session
or change the app's presentation. The CLI's session, pane and terminal commands
also work when that switch is off. To turn it off permanently, change it in
Rex and use `./dotfiles/install.sh --pull` to record the preference.

Closing or quitting the GUI does not have the same meaning as stopping the
server. Sessions run in the server; stopping it ends their programs. A machine
restart ends running processes, so resume the Claude or Codex conversation
afterwards rather than expecting a live agent to survive a reboot.

## Inspect and maintain

```sh
rex ls
rex session inspect --json
rex skill status
rex terminfo status
rex config check
rex config reload
rex keymap
```

Inside Rex these target the current session. From another terminal, name a
session with `-s NAME`. `rex new NAME --cwd "$PWD"` creates a session on the
server; choose it in the app's session switcher to view it. For automation,
save full IDs from `--json`, because labels can change or be ambiguous.

App-level shortcut overrides take precedence over `init.lua`. If a shortcut
does not behave as configured, inspect Rex's Shortcuts settings and `rex keymap`.
After an update, rerun the dotfile installer to refresh generated integration
and completion files. Use `rex help` for the installed version's commands.

Private hosts and local overrides belong in `~/.config/rex/private.lua`, which
`init.lua` loads last. Neither that file, Rex's host lists, its state directory,
nor its full macOS preference file is copied into this public repo.
`XDG_CONFIG_HOME` and `XDG_DATA_HOME` are respected. If set, make sure Rex's
server inherits the same config directory; setting it only in a terminal does
not move a server that is already running.

Sources: [CLI](https://www.superlogical.com/rex/docs/automate/cli),
[agent setup](https://www.superlogical.com/rex/docs/automate/agent-skill),
[configuration](https://www.superlogical.com/rex/docs/customize/config),
[shortcuts](https://www.superlogical.com/rex/docs/customize/keyboard-shortcuts),
and the installed CLI's `rex __internal skill` and command help.
