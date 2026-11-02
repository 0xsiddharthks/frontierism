# frontierism

Building the new Frontier.

- [`skills/`](skills/README.md): my agent skills for Claude Code and Codex.
- [`mods/`](mods/README.md): my Claude Code mods. `/prs` opens a pane of my open PRs as stacks, with CI and review state.
- [`provision/`](provision/README.md): what I install on a new Mac: Homebrew with its formulae and casks, and a few tools from their own installers. Run this first on a new machine.
- [`dotfiles/`](dotfiles/README.md): my terminal, shell, editor and agent config, with an installer for a new machine. It also installs [`cw`](dotfiles/README.md#cw), which starts Claude Code in its own git worktree: `cw [name]`.
- [`preferences/`](preferences/README.md): app defaults to apply afterwards, including Zed for code/text files and Codex's Open in actions, and Vim for Git editing. Run `./preferences/install.sh`; `--check` only reports differences.
