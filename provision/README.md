# Provision

What I install on a new Mac: Homebrew and its formulae and casks, and a few tools that come from their own installers.

| Here         | What it is                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------- |
| `Brewfile`   | The taps, formulae and casks, as `brew bundle dump` writes them.                            |
| `install.sh` | Installs Homebrew, whatever in the `Brewfile` isn't installed yet, and the [tools](#tools). |

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

| Tool        | Installer                              |
| ----------- | -------------------------------------- |
| rustup      | `https://sh.rustup.rs`                 |
| Claude Code | `https://claude.ai/install.sh`         |
| Codex       | `https://chatgpt.com/codex/install.sh` |
| herdr       | `https://herdr.dev/install.sh`         |

Not kept here: apps from the App Store or installed by hand, other tools that came from their own installers, such as uv, and what was installed with `cargo`, `go`, `uv` or `npm`. The VS Code extensions are in the [dotfiles](../dotfiles/README.md).

## New machine

1. Run `xcode-select --install` and wait for it to finish. It brings git.
2. Copy `~/.Brewfile.private` over from the old Mac, to have what it lists installed too.
3. Clone this repo to the path the skills expect, and run the installer:

   ```sh
   git clone https://github.com/0xsiddharthks/frontierism.git ~/Developer/0xsiddharthks/frontierism
   ~/Developer/0xsiddharthks/frontierism/provision/install.sh
   ```

   Homebrew's installer asks for a password first, and so do some of the casks along the way. If something fails to install, run it again.

4. Open a new terminal, so that what was installed is on `PATH`.
5. Carry on with the [dotfiles](../dotfiles/README.md#new-machine).
