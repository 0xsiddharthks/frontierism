---
name: herdr-core
description: Run, inspect or coordinate terminals and programs with herdr-core (hc), using its installed guide. Use when the request calls for herdr-core operations; desktop layout changes belong to herdr-app.
---

# Herdr core

Read `hc --skill` and follow its current instructions before acting. Use the
installed command's help for exact arguments when needed.

Core runs the terminals; `herdr-app --skill` covers the desktop window. The
legacy `herdr` TUI has a separate server and guide.

Keep this wrapper thin. Read upstream guidance from the installed binary on each
invocation rather than copying it here; upgrades then supply the current manual.
