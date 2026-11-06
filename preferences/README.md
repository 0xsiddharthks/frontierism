# Preferences

macOS and app defaults to apply after [provision](../provision/README.md) installs the apps
and [dotfiles](../dotfiles/README.md) copies their configuration. This step changes
app preferences and macOS file associations rather than copying entire settings
stores into this public repo.

```sh
./preferences/install.sh          # apply the defaults and verify them
./preferences/install.sh --check  # report differences without applying changes
```

Run it on each new Mac after provision and dotfiles. Repeated runs are safe; a run
with nothing to change creates no backup. Quit Claude before applying a changed
editor preference. Reopen ChatGPT/Codex after changing its preferences, and open a
new terminal to pick up the shell's `EDITOR` and `VISUAL` values.
macOS may ask whether to keep the previous app or **Use Cursor** for a group of file
types. Choose **Use Cursor**; the script waits for confirmation and verifies the result.

## Automatic appearance

The installer sets macOS Appearance to **Auto** so system-following apps use light
mode during the day and dark mode at night. It checks the saved
`AppleInterfaceStyleSwitchesAutomatically` preference and changes only that key.
Herdr app, the Herdr TUI through Ghostty and Cursor already follow system
appearance in their dotfiles. `--check` reports if Auto has been turned off.

## Editor defaults

[`editor.json`](editor.json) is the list to maintain. It selects Cursor for:

- Code and plain-text file types in macOS, including Rust, Cargo/TOML, Markdown,
  TXT, source languages, scripts, configuration files and diffs. Broad text/source
  types provide a fallback; explicit extensions replace older specific choices.
- Files and repositories opened from Codex. Existing per-project editor overrides
  are cleared so they inherit Cursor. This uses Codex's configuration API to update
  selected settings in its local `config.toml`.
- Codex CLI file links, through `file_opener = "cursor"`.
- Claude desktop's **Open in** actions, through the selected editor preference in
  `preferences.epitaxyPrefs` inside `claude_desktop_config.json`. Only that field is
  merged; MCP servers, sign-ins and other local preferences are preserved.

Other apps, including ChatGPT, use Cursor when opening code/text files through the
macOS default. Herdr's editor action and `Cmd+Shift+O` also open Cursor through its
CLI, configured by the dotfiles.

[GitHub Desktop supports Cursor](https://docs.github.com/en/desktop/configuring-and-customizing-github-desktop/configuring-a-default-editor-in-github-desktop).
On a clean Mac it selects and remembers Cursor automatically because provision
installs no other supported GUI code editor. GitHub Desktop stores its explicit
choice in its private Chromium storage, which these scripts do not edit. If using
an existing profile or installing another editor separately, select **GitHub
Desktop → Settings → Integrations → External Editor → Cursor** once.

Git's global `core.editor` uses `vim` for commit messages, amend and interactive
rebase. The dotfiles also set `EDITOR` and `VISUAL` to `vim` for terminal editing.
Vim is included with macOS and checked by provision; no Homebrew package is needed.

macOS folder handlers, web links, images, PDFs, office documents and spreadsheet
associations are outside
this file-type list. HTML also keeps its browser handler: macOS treats changing
the HTML default through this API as changing the default web browser.
Extensionless files use the content type macOS recognizes.

## Codex project roots

The same preferences step sets these portable values in `~/.codex/config.toml`:

```toml
project_root_markers = [".codex-root"]
project_doc_max_bytes = 65536
file_opener = "cursor"
```

The empty [`.codex-root`](../.codex-root) marker is committed at this repository's
root, so a normal clone already includes it. Codex uses that marker instead of
`.git` when discovering the project root, including when working inside a nested
repository beneath this project. The instruction size limit keeps the current
64 KiB allowance for project guidance. Add a `.codex-root` marker to other projects
where the same explicit root discovery is wanted.

The helper writes only the listed keys through Codex's configuration API. It
preserves unrelated settings and TOML comments. It does not copy authentication,
session history, paths or project trust decisions from the old Mac; sign in and
trust the checkout on the new Mac as usual.

## Applying and backups

The helper uses Apple's
[default-application API](https://developer.apple.com/documentation/appkit/nsworkspace/setdefaultapplication(at:toopen:completion:))
and the installed Codex CLI's
[configuration API](https://learn.chatgpt.com/docs/app-server#config-rpc-examples-for-app-settings).
It sends configuration requests only, without starting a Codex chat or a model run.
Apple's Command Line Tools, installed during provision, compile the small native
helper into a local cache on its first use. Using the current macOS API also covers
uncommon extensions with dynamic content types that older association tools reject.

Before making changes it saves only the previous file handlers, selected Codex
settings, Claude editor choice, Git editor and automatic appearance setting to
`~/.local/state/frontierism/preferences/` (or under
`XDG_STATE_HOME`). Backups are private local files and never enter the repo.
They record the previous handlers for restoring an association through Finder's
**Get Info → Open with → Change All**; `null` means no previous default could be
resolved. The appearance value is `true`, `false` or `null` for an unset key.
No other app preferences or Codex state are exported.
