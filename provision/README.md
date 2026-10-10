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
   ./provision/install.sh
   ```

   It installs three things, in this order:
   - Homebrew. Its installer says what it will do, waits for Return, and asks for the password.
   - Everything in the `Brewfile`. This is the long part, and some casks ask for the password again.
   - rustup, Claude Code, Codex, herdr and Oh My Zsh.

   If something fails to install, run it again. It skips what is already there.

6. Open a new terminal, so that what was installed is on `PATH`, and check that nothing is missing:

   ```sh
   cd ~/Developer/0xsiddharthks/frontierism
   ./provision/install.sh --check
   ```

   Every line should start with `ok`.

7. Carry on with the [dotfiles](../dotfiles/README.md#new-machine), which copy my config into place, install the VS Code extensions and link the skills and mods.

Still to install by hand: apps from the App Store, apps that aren't in Homebrew, other tools that have their own installers, such as uv, and whatever was installed with `cargo`, `go`, `uv` or `npm`.

## Use

```sh
./install.sh          # install Homebrew, the tools, and what is missing from the Brewfile
./install.sh --check  # only report
./install.sh --pull   # rewrite the Brewfile from what is installed here, to review and commit
```

An entry in the `Brewfile` that isn't installed here is `missing`, and one that is installed here but isn't in the `Brewfile` is `unlisted`. Nothing is uninstalled, and nothing already installed is upgraded unless a new install needs it.

After installing or removing something with `brew`, run `--pull` and commit. After adding a line here, run `./install.sh`. `--pull` replaces the whole file, so run it on the Mac that has everything; comments and ordering of your own don't survive it.

Homebrew only loads a formula or cask from a third-party tap once it has been told to trust it. The `Brewfile` carries that as `trusted: true`, so a new Mac trusts the same ones. Something that is installed but not trusted is left out by `brew bundle dump`, and reported here as `skipped`.

## Kept out of this repo

This repo is public. A formula or cask that I'd rather not list in it goes in `~/.Brewfile.private`, written as it would be in the `Brewfile`:

```ruby
cask "some-app"
```

The installer installs from both files, and `--pull` leaves those entries out of the `Brewfile`. `--pull` refuses to run on a Mac that doesn't have the file, because it would put everything installed there into the `Brewfile`. An empty file is enough to say that nothing is private.

## Tools

These have their own installers and update themselves, so they aren't taken from Homebrew. Each is installed only if it isn't there yet.

| Tool        | Installer                                                                   |
| ----------- | --------------------------------------------------------------------------- |
| rustup      | `https://sh.rustup.rs`                                                      |
| Claude Code | `https://claude.ai/install.sh`                                              |
| Codex       | `https://chatgpt.com/codex/install.sh`                                      |
| herdr       | `https://herdr.dev/install.sh`                                              |
| Oh My Zsh   | `https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh` |

Oh My Zsh's installer writes a starter `~/.zshrc` when there isn't one, and leaves one that is there alone. The [dotfiles](../dotfiles/README.md#zsh) put mine in its place.
