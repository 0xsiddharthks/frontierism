# Provision

What I install on a new Mac: Homebrew and its formulae and casks, and a few tools that come from their own installers.

| Here         | What it is                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------- |
| `Brewfile`   | The taps, formulae and casks, as `brew bundle dump` writes them.                            |
| `install.sh` | Installs Homebrew, whatever in the `Brewfile` isn't installed yet, and the [tools](#tools). |

## New machine

From a Mac with nothing on it to one that has everything here:

1. Create the macOS account with the account name `siddharthks`. The skills and the Claude settings name files by their full path under `/Users/siddharthks`.
2. Bring `~/.Brewfile.private` over from the old Mac and put it in the home folder. It lists the apps [kept out of this repo](#kept-out-of-this-repo), and they are only installed if it is there. Bring `~/.zshrc.private` at the same time, for the [dotfiles](../dotfiles/README.md#zsh).
3. Install Apple's Command Line Tools, which bring git, and wait for that to finish:

   ```sh
   xcode-select --install
   ```

4. Clone this repo to the path the skills expect:

   ```sh
   git clone https://github.com/0xsiddharthks/frontierism.git ~/Developer/0xsiddharthks/frontierism
   cd ~/Developer/0xsiddharthks/frontierism
   ```

   That is over HTTPS, because a new Mac has no SSH key yet. To push from it later, add a key to GitHub and run `git remote set-url origin git@github.com:0xsiddharthks/frontierism.git`.

5. Run the installer:

   ```sh
   ./setup/provision/install.sh
   ```

   It installs three things, in this order:
   - Homebrew. Its installer says what it will do, waits for Return, and asks for the password.
   - Everything in the `Brewfile`. This is the long part, and some casks ask for the password again.
   - rustup, Claude Code, Codex, the Herdr TUI, Herdr desktop app, herdr-core and Oh My Zsh.

   If something fails to install, run it again. It skips what is already there.
   It also checks that Vim, included with macOS, is available for terminal editing.

6. Open a new terminal, so that what was installed is on `PATH`, and check that nothing is missing:

   ```sh
   cd ~/Developer/0xsiddharthks/frontierism
   ./setup/provision/install.sh --check
   ```

   Every line should start with `ok`.

7. Install [Rex Beta from its DMG](https://blob.superlogical.com/download/rex-app/preview/latest.dmg)
   by dragging `Rex Beta.app` into `/Applications`. This stays manual during the
   beta; neither this installer nor the Brewfile downloads it.

8. Carry on with the [dotfiles](../dotfiles/README.md), which copy my config into place and set up Cursor, the only GUI code editor installed here. Cursor gets its saved settings, keyboard shortcuts, extensions and selected app preferences. Close Cursor first so those app preferences can be applied. The dotfiles also configure Herdr's personal layout, themes and keybindings, and the installed Rex app for Claude Code and Codex automatically. `--push` replaces starter configs written by app installers, keeping backups. Then run `./setup/install.sh` to link the skills and mods.

   ```sh
   ./setup/dotfiles/install.sh --push
   ./setup/dotfiles/install.sh --check
   ./setup/install.sh
   ```

   Open a fresh terminal afterwards. Rex's [workflow guide](../dotfiles/rex/README.md)
   describes its shortcuts and the one-time Codex hook approval.

9. Apply the [macOS and app preferences](../preferences/README.md), which enable
   automatic day/night appearance and make Cursor the default for code/text files
   and app integrations. This also configures Codex's `.codex-root` discovery.
   Git editing uses Vim, matching the dotfiles' `EDITOR` and `VISUAL` settings:

   ```sh
   ./setup/preferences/install.sh
   ./setup/preferences/install.sh --check
   ```

   Reopen Codex after applying its editor preference.

Still to install by hand: apps from the App Store, apps that aren't in Homebrew, other tools that have their own installers, such as uv, and whatever was installed with `cargo`, `go`, `uv` or `npm`.

## Use

From the repo root:

```sh
./setup/provision/install.sh          # install Homebrew, tools, and what is missing from the Brewfile
./setup/provision/install.sh --check  # only report
./setup/provision/install.sh --pull   # rewrite the Brewfile from what is installed here, to review and commit
```

An entry in the `Brewfile` that isn't installed here is `missing`, and one that is installed here but isn't in the `Brewfile` is `unlisted`. Nothing is uninstalled, and nothing already installed is upgraded unless a new install needs it.

Cursor is the only GUI code editor in this setup. VS Code and Zed, including their
Insiders/Preview casks, are excluded from installs and `--pull`, even if an older
Mac or private Brewfile still lists them. Existing installations are reported as
`unlisted`; the scripts do not uninstall apps from the current Mac.

After installing or removing something with `brew`, run `./setup/provision/install.sh --pull` and commit. After adding a line here, run `./setup/provision/install.sh`. Run `--pull` on the Mac that has everything because it rewrites the Brewfile in Homebrew's order and drops custom comments.

Homebrew only loads a formula or cask from a third-party tap once it has been told to trust it. The `Brewfile` carries that as `trusted: true`, so a new Mac trusts the same ones. Something that is installed but not trusted is left out by `brew bundle dump`, and reported here as `skipped`.

## Kept out of this repo

This repo is public. A formula or cask that I'd rather not list in it goes in `~/.Brewfile.private`, written as it would be in the `Brewfile`:

```ruby
cask "some-app"
```

The installer installs from both files, and `--pull` leaves those entries out of the `Brewfile`. `--pull` refuses to run on a Mac that doesn't have the file, because it would put everything installed there into the `Brewfile`. An empty file is enough to say that nothing is private.

## Tools

These have their own installers and update themselves, so they aren't taken from Homebrew. Each is installed only if it isn't there yet.

The installer also ensures rustup has `rust-src`, `rustfmt` and `clippy` for editor
analysis, formatting and linting, including on Macs where Rust is already installed.

| Tool        | Installer                                                                   |
| ----------- | --------------------------------------------------------------------------- |
| rustup      | `https://sh.rustup.rs`                                                      |
| Claude Code | `https://claude.ai/install.sh`                                              |
| Codex       | `https://chatgpt.com/codex/install.sh`                                      |
| herdr       | `https://herdr.dev/install.sh`                                              |
| Herdr app   | `https://releases.herdr.dev/app/install.sh`                                 |
| herdr-core  | `https://releases.herdr.dev/core/install.sh`                                |
| Oh My Zsh   | `https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh` |

Oh My Zsh's installer writes a starter `~/.zshrc` when there isn't one, and leaves one that is there alone. The [dotfiles](../dotfiles/README.md#zsh) put mine in its place.

Herdr app installs to `~/Applications/Herdr.app` with its `herdr-app` CLI in
`~/.local/bin`. The app installer also installs a missing core; this provisioner
checks `~/.local/bin/herdr-core` separately and ensures its `hc` shortcut exists.
The app and core update themselves. The [personal Herdr files](../dotfiles/herdr-app/README.md)
are applied by the dotfile installer, including before the app's first launch.
