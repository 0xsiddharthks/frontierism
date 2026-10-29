# Herdr app

Personal configuration for the desktop app, migrated from `~/.config/herdr/config.toml`.
The desktop app and the older `herdr` TUI are separate programs. The TUI config is
still kept in [`../herdr/config.toml`](../herdr/config.toml). Both use Tokyo Night
Day for light appearance and Tokyo Night for dark appearance.

The [official app installer](https://releases.herdr.dev/app/install.sh) installs
`~/Applications/Herdr.app`, `~/.local/bin/herdr-app`, and herdr-core when missing.
[`../../provision/install.sh`](../../provision/install.sh) checks the app and core
separately, and ensures the `hc` shortcut exists. The TUI remains installed for
its existing shell helpers and integrations.

## Install and sync

On a new Mac, from the repository root:

```sh
./provision/install.sh
./dotfiles/install.sh --push
./dotfiles/install.sh --check
```

`--push` is necessary when the app has already created default settings or keys.
To apply or check only Herdr without touching the other dotfiles:

```sh
./dotfiles/herdr-app/setup.py --push
./dotfiles/herdr-app/setup.py --check
```

A plain run adds missing files and reports drift. `--push` backs up changed home
files beside them as `.bak-<time>`; identical files create no backups. `--pull`
copies only the managed settings, keys, themes, personal layout and three personal
mods back here, refusing obvious credentials. Review the diff before committing.
The installer respects `HERDR_APP_HOME`, defaulting to `~/.config/herdr-app`.

An apply checks all three mods. If Herdr is open, it selects the `frontierism` layout
and verifies the running app's error list. Otherwise it saves the layout choice
and completed onboarding for the next launch, preserving unrelated shared state.
It never launches or restarts the app or core. `--check` only reports.

Only personal configuration travels to the new machine. Live terminals, SSH
machines, session IDs, window positions, layout click state, telemetry, generated
`AGENTS.md` and type declarations stay local. `--pull` does not export UI changes
stored only in `layouts/.state`; make persistent layout changes in the JSON here.

## Daily workspace

The workspace keeps the task visible and its controls reachable:

macOS's **Auto** appearance setting controls the day/night schedule. Herdr app
follows the system directly; the TUI follows its host terminal's appearance. The
tracked Ghostty config already switches between light and dark with macOS.

- JetBrains Mono at 16 px, automatic light/dark Tokyo Night, muted sounds and compact terminal
  padding. The UI keeps its normal size; the extra space goes to terminal text.
- A persistent header shows the focused terminal's title, program, folder,
  branch and status. Single terminals have no duplicate pane header; split panes
  keep their own labels and focus borders.
- Files, Changes, Zed and the new-terminal/agent menu stay available when there is
  one tab and its strip is hidden. Files and Changes remember their selection
  independently for each space. Zed opens the focused local folder, and is omitted
  for remote spaces rather than opening a remote path on this Mac.
- The sidebar gives more room to the attention queue. Agent rows show the task
  title, then program, space and branch; hover for the full folder and title.
  Priority sorting, pins, subagents and static status symbols remain available.

The header is the personal `frontier-workbench` mod. It uses Herdr's live model
without polling. Its Zed action runs `zed <folder>` only when requested by a click
or key; it does not start an editor on launch. Existing terminals and sessions
are unaffected by configuration reloads.

## Migrated preferences

| Old setting | Desktop equivalent |
| --- | --- |
| `theme` | Tokyo Night Day / Tokyo Night follow macOS appearance. No forced `appearance` override. The TUI uses `auto_switch = true` to follow its host terminal; the tracked Ghostty config already follows macOS. |
| `switch_workspace = "prefix+1..9"` | Desktop uses `Cmd+1`–`Cmd+9` for spaces; the TUI retains its prefix binding. |
| `switch_tab = ""` | No numeric tab-selection bindings. |
| `status_indicators = "symbols"` | Static `!`, `~`, `✓`, `○` symbols in the agents list and tab strip. |
| `show_agent_labels_on_pane_borders = true` | Split pane headers show each agent's program name; the workspace header identifies a single terminal. |
| `agent_panel_sort = "priority"` | The personal agents mod starts with priority sorting; pins, groups and subagents retain the shipped behavior. |
| `rows = [["state_icon", "terminal_title_stripped"], ["agent"]]` | Status and cleaned terminal title on the first line; agent name with space and branch context on the second. |
| `hide_tab_bar_when_single_tab = true` | The strip appears only with two or more tabs; the persistent header keeps controls reachable at zero or one. |
| `ui.sound.enabled = false` | `sounds.enabled = false`. |
| `onboarding = false` | The setup records completed onboarding; it closes only the welcome overlay if already open. |

The personal layout, agents list and tab strip are clones of Herdr app 0.1.7's
`main`, `agents` and `tabs`; the persistent header is a personal mod. Shipped files
remain app-managed. Herdr updates those files on startup;
the personal copies survive. The light/dark theme pair on the personal layout
replaces the clone's inherited theme choice; macOS decides which half is active.

These old options have no configurable equivalent in the installed 0.1.7 API:

- `window_title = "{terminal_title}"`: the native window title is controlled by
  the app; the terminal title is visible in the workspace header and agents list.
- `ui.toast.delivery = "terminal"`: a native window has no outer terminal to
  deliver notifications through. Herdr's in-app notifications remain available.
- `experimental.pane_history = true`: core owns terminal scrollback (5 MB per live
  terminal by default), with no matching history-across-restarts toggle. Closing
  the window keeps terminals alive; recovery after a reboot starts fresh shells.

## Keys

The desktop uses Mac shortcuts. `Ctrl+B` goes directly to the terminal again;
there is no prefix mode in the desktop configuration. This avoids a timed chord
stealing the shell's backward-character shortcut. The legacy TUI keeps its
existing `Ctrl+B` bindings because it runs inside another terminal.

| Desktop key | Action |
| --- | --- |
| `Cmd+1`–`Cmd+9` | Select space |
| `Cmd+T`, `Ctrl+Tab`, `Ctrl+Shift+Tab` | New, next, previous tab |
| `Cmd+N`, `Cmd+P` | New space, space picker |
| `Cmd+]`, `Cmd+[` | Next, previous agent in sidebar order |
| `Cmd+D`, `Cmd+Shift+D` | Split right, down |
| `Cmd+Option+arrows` | Focus a pane |
| `Cmd+Shift+Enter` | Zoom the focused pane |
| `Cmd+W`, `Cmd+Shift+W` | Close tab, close pane |
| `Cmd+Shift+E`, `Cmd+Shift+G` | Toggle Files, Changes |
| `Cmd+Shift+O` | Open the focused local folder in Zed |
| `Cmd+B`, `Cmd+,`, `Cmd+Shift+P` | Toggle sidebar, settings, command palette |

Panel and editor shortcuts apply while the personal layout is shown. Plain
control-key editing stays with terminal programs.

TUI-only operations such as detaching an outer terminal and entering its resize
mode have no prefix binding here. Resize splits with their native dividers.
The reserved escape hatch is `Ctrl+Alt+Shift+Escape`; it resets the shown layout
and keys to Herdr's defaults, keeping the old files aside.

## Validation and sources

```sh
herdr-app check ~/.config/herdr-app/mods/frontier-agents
herdr-app check ~/.config/herdr-app/mods/frontier-tabs
herdr-app check ~/.config/herdr-app/mods/frontier-workbench
herdr-app status
herdr-app shot /tmp/herdr.png
python3 -m unittest discover -s dotfiles/herdr-app -p 'test_*.py'
node dotfiles/herdr-app/test_mods.mjs
```

Read `herdr-app --skill` and the installed `~/.config/herdr-app/AGENTS.md` before
changing APIs or layout structure. The installed guide and `.d.ts` files describe
the actual version; they are not copied into this repository.

The mod and layout clones come from [herdrdev/herdr-app](https://github.com/herdrdev/herdr-app)
under the [Apache 2.0 license](LICENSE). The terminal palettes come from
[Tokyo Night's Night](https://github.com/folke/tokyonight.nvim/blob/main/extras/ghostty/tokyonight_night)
and [Day](https://github.com/folke/tokyonight.nvim/blob/main/extras/ghostty/tokyonight_day)
themes. The included SVG is a schematic layout preview, not a screenshot of a session.
