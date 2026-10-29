---
name: herdr-app
description: Configure or operate the Herdr desktop app, including its layouts, appearance, keys and mods, using the installed guide. Use for the desktop window rather than the legacy Herdr TUI.
---

# Herdr desktop app

Read `herdr-app --skill` and follow its current instructions before acting.
For customization, it directs you to the generated `AGENTS.md` and API types in
`${HERDR_APP_HOME:-$HOME/.config/herdr-app}`; read the relevant installed files.

The window uses `herdr-app`; running terminals and programs use `hc --skill`.
The legacy `herdr` TUI is a separate program.

Keep this wrapper thin. Read upstream guidance from the installed binary on each
invocation rather than copying it here; upgrades then supply the current manual.
