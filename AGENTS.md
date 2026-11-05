# Public repo

- Treat everything committed to this repo as publicly readable. This applies to code, skills, dotfiles, examples, generated files, logs, screenshots, commit messages, and pull request descriptions.
- Never commit secrets: API keys, access tokens, passwords, private keys, wallet seed phrases, recovery codes, session cookies, authorization headers, or credential files. Use environment variables or local, ignored files; keep examples to clearly fake placeholders.
- Never commit personal or private information, such as home addresses, private contact details, financial or medical records, private correspondence, or nonpublic documents. Public profile information and intentionally public project details are fine; access to a connected app or local file does not make its contents public.
- Never commit Mysten-internal or other confidential work details, including internal hostnames, account or resource IDs, and incident details. Generalize examples and remove private identifiers before including them.
- Before committing or pushing, review the exact staged changes for secrets and private information, including new files and generated output. Check commit author/committer emails and file metadata too; use intentionally public identity details or the user's GitHub noreply address. Stage only intended files; `.gitignore` does not protect files already tracked by Git.
- If you find sensitive material, do not repeat its value in chat, logs, or commit messages. Report its file and location with the value redacted, remove it from the proposed changes, and tell the user if it may already be in Git history. Exposed credentials need revocation or rotation; deleting the current file does not remove earlier commits. Do not rewrite published history without explicit authorization.

# Codex and ChatGPT Work

- If you are Codex (or ChatGPT Work): prefer ChatGPT's built-in `@Browser`. Use `@Chrome` only when I ask for it or when the needed authenticated session isn't available in the built-in browser.

# Notion notes

- Notion is the primary reading and editing workspace. Use Obsidian only when a task specifically calls for it.
- Use list views for Notion hubs and collections of nested pages. Do not use table views unless I explicitly request one. Keep only a few useful properties beside each title; organize fuller metadata within the page's details.
- Omit page icons from study pages and guides to keep their headers compact.

# Attribution

- Sessions started in this repo may sign their work: end commit messages with your own co-author trailer (for Codex, `Co-authored-by: Codex <noreply@openai.com>`), and add your usual generated-with line to pull request descriptions. Sessions started in another repo follow that repo's rule instead.

# Pushing

- Only I work in this repo, so don't push a branch or open a pull request for your work. Fast-forward `origin/main` to it whenever possible, including from a worktree branch (`git push origin HEAD:main`).
- Every time you do, pull any upstream changes first (`git pull --rebase origin main`), so that the push fast-forwards.
