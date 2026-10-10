# Public repo

- This repo is public. Never put credentials in it, or Mysten-internal details such as internal hostnames, account or resource IDs, and incident details. That covers skills, dotfiles and commit messages.

# Codex and ChatGPT Work

- If you are Codex (or ChatGPT Work): prefer ChatGPT's built-in `@Browser`. Use `@Chrome` only when I ask for it or when the needed authenticated session isn't available in the built-in browser.

# Attribution

- Sessions started in this repo may sign their work: end commit messages with your own co-author trailer (for Codex, `Co-authored-by: Codex <noreply@openai.com>`), and add your usual generated-with line to pull request descriptions. Sessions started in another repo follow that repo's rule instead.

# Pushing

- Only I work in this repo, so don't push a branch or open a pull request for your work. Fast-forward `origin/main` to it whenever possible, including from a worktree branch (`git push origin HEAD:main`).
- Every time you do, pull any upstream changes first (`git pull --rebase origin main`), so that the push fast-forwards.
