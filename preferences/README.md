# Preferences

App defaults to apply after [provision](../provision/README.md) installs the apps
and [dotfiles](../dotfiles/README.md) copies their configuration. This step changes
app preferences and macOS file associations rather than copying entire settings
stores into this public repo.

```sh
./preferences/install.sh          # apply the defaults and verify them
./preferences/install.sh --check  # report differences without applying changes
```

Run it on each new Mac after provision and dotfiles. Repeated runs are safe; a run
with nothing to change creates no backup. Reopen Codex after changing its preferred
editor, and open a new terminal to pick up the shell's `EDITOR` and `VISUAL` values.
macOS may ask whether to keep the previous app or **Use Zed** for a group of file
types. Choose **Use Zed**; the script waits for confirmation and verifies the result.

## Editor defaults

[`editor.json`](editor.json) is the list to maintain. It selects Zed for:

- Code and plain-text file types in macOS, including Rust, Cargo/TOML, Markdown,
  TXT, source languages, scripts, configuration files and diffs. Broad text/source
  types provide a fallback; explicit extensions replace older specific choices.
- Files and repositories opened from Codex. Existing per-project editor overrides
  are cleared so they inherit Zed. This uses Codex's configuration API to update
  only `desktop.open-in-target-preferences` in its local `config.toml`.
- Git's global `core.editor`, using `zed --wait` so Git waits for editing to finish.

The dotfiles also set `EDITOR` and `VISUAL` to `zed --wait`. macOS folder handlers,
web links, images, PDFs, office documents and spreadsheet associations are outside
this file-type list. HTML also keeps its browser handler: macOS treats changing
the HTML default through this API as changing the default web browser.
Extensionless files use the content type macOS recognizes.

The helper uses Apple's
[default-application API](https://developer.apple.com/documentation/appkit/nsworkspace/setdefaultapplication(at:toopen:completion:))
and the installed Codex CLI's
[configuration API](https://learn.chatgpt.com/docs/app-server#config-rpc-examples-for-app-settings).
It sends configuration requests only, without starting a Codex chat or a model run.
Apple's Command Line Tools, installed during provision, compile the small native
helper into a local cache on its first use. Using the current macOS API also covers
uncommon extensions with dynamic content types that older association tools reject.

Before making changes it saves only the previous file handlers, Codex editor
choice and Git editor to `~/.local/state/frontierism/preferences/` (or under
`XDG_STATE_HOME`). Backups are private local files and never enter the repo.
They record the previous handlers for restoring an association through Finder's
**Get Info → Open with → Change All**; `null` means no previous default could be
resolved. No other app preferences or Codex state are exported.
