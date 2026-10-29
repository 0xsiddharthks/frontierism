# Herdr app

Personal configuration for the desktop app, migrated from `~/.config/herdr/config.toml`.
The desktop app and the older `herdr` TUI are separate programs. The TUI config is
still kept in [`../herdr/config.toml`](../herdr/config.toml); its fixed dark appearance
now matches the live file too.

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
copies only the managed settings, keys, themes, personal layout and two personal
mods back here, refusing obvious credentials. Review the diff before committing.
The installer respects `HERDR_APP_HOME`, defaulting to `~/.config/herdr-app`.

An apply checks both mods. If Herdr is open, it selects the `frontierism` layout
and verifies the running app's error list. Otherwise it saves the layout choice
and completed onboarding for the next launch, preserving unrelated shared state.
It never launches or restarts the app or core. `--check` only reports.

Only personal configuration travels to the new machine. Live terminals, SSH
machines, session IDs, window positions, layout click state, telemetry, generated
`AGENTS.md` and type declarations stay local. `--pull` does not export UI changes
stored only in `layouts/.state`; make persistent layout changes in the JSON here.

## Migrated preferences

| Old setting | Desktop equivalent |
| --- | --- |
| `theme.name = "tokyo-night"`, `auto_switch = false` | Fixed Tokyo Night in `settings.json` and the personal layout, with dark appearance. A dormant Tokyo Night Day theme is included for manual use. |
| `switch_workspace = "prefix+1..9"` | `Ctrl+B`, then `1`–`9` selects a space. |
| `switch_tab = ""` | No numeric tab-selection bindings. |
| `status_indicators = "symbols"` | Static `!`, `~`, `✓`, `○` symbols in the agents list and tab strip. |
| `show_agent_labels_on_pane_borders = true` | The shipped pane header shows each agent's program name. |
| `agent_panel_sort = "priority"` | The personal agents mod starts with priority sorting; pins, groups and subagents retain the shipped behavior. |
| `rows = [["state_icon", "terminal_title_stripped"], ["agent"]]` | Status and cleaned terminal title on the first line; agent name on the second. |
| `hide_tab_bar_when_single_tab = true` | The personal tabs mod hides the strip at exactly one tab and restores it at zero or two or more. |
| `ui.sound.enabled = false` | `sounds.enabled = false`. |
| `onboarding = false` | The setup records completed onboarding; it closes only the welcome overlay if already open. |

The personal layout and mods are clones of Herdr app 0.1.7's `main`, `agents` and
`tabs`. Shipped files remain app-managed. Herdr updates those files on startup;
the personal copies survive. The explicit theme on the personal layout prevents
the clone's inherited Graphite theme choice from overriding the migrated color.

These old options have no configurable equivalent in the installed 0.1.7 API:

- `window_title = "{terminal_title}"`: the native window title is controlled by
  the app; the terminal title remains visible in the agents list.
- `ui.toast.delivery = "terminal"`: a native window has no outer terminal to
  deliver notifications through. Herdr's in-app notifications remain available.
- `experimental.pane_history = true`: core owns terminal scrollback (5 MB per live
  terminal by default), with no matching history-across-restarts toggle. Closing
  the window keeps terminals alive; recovery after a reboot starts fresh shells.

## Keys

The old prefix is `Ctrl+B`; a space in `keys.json` separates successive strokes.
`Ctrl+B`, then `Ctrl+B` sends a literal Ctrl+B to the terminal. This intentionally
reserves a single Ctrl+B, formerly the shell's backward-character shortcut.
Mac shortcuts for copying, pasting, splitting, zoom and the command palette stay
available alongside these familiar TUI bindings:

| After `Ctrl+B` | Action |
| --- | --- |
| `1`–`9` | Select space |
| `c`, `p`, `n` | New, previous, next tab |
| `Shift+T`, `Shift+X` | Rename, close tab |
| `Shift+N`, `Shift+W`, `Shift+D` | New, rename, close space |
| `h`, `j`, `k`, `l` | Focus left, down, up, right pane |
| `v`, `-` | Split right, down |
| `x`, `z` | Close, zoom pane |
| `b`, `w`, `s`, `?` | Toggle sidebar, space picker, settings, help |

TUI-only operations such as detaching an outer terminal and entering its resize
mode have no prefix binding here. Resize splits with their native dividers.
The reserved escape hatch is `Ctrl+Alt+Shift+Escape`; it resets the shown layout
and keys to Herdr's defaults, keeping the old files aside.

## Validation and sources

```sh
herdr-app check ~/.config/herdr-app/mods/frontier-agents
herdr-app check ~/.config/herdr-app/mods/frontier-tabs
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
