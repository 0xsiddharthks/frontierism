# Legacy Obsidian workflow entrypoint

Obsidian export and cross-page analysis now have their own reusable skills:

- [notion-to-obsidian](../../notion-to-obsidian/SKILL.md): export a fully fetched Notion page or bounded hub into a chosen vault, with local embeds and a repeatable page-ID mapping.
- [notion-analyze-and-link](../../notion-analyze-and-link/SKILL.md): review and connect the maintained Notion notes.
- [obsidian-analyze-and-link](../../obsidian-analyze-and-link/SKILL.md): review and connect local notes when an Obsidian task is requested.

Existing vaults, private course profiles, and publication ledgers do not need migration. Legacy `scripts/export_obsidian.py` and `references/obsidian.css` paths forward to the exporter skill so existing private scripts keep working. Using the Predictive History publisher alone does not modify an Obsidian vault or launch a connection pass.
