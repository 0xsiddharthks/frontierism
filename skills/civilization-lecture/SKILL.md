---
name: civilization-lecture
description: Compatibility entrypoint for existing Civilization Notion study pages and legacy helper paths. Use predictive-history for lecture publishing.
---

# Civilization compatibility entrypoint

Read [the Predictive History skill](../predictive-history/SKILL.md) and follow its workflow. This entrypoint preserves existing references to `$civilization-lecture` and its helper paths; the shared implementation lives in `predictive-history`.

For an existing Civilization archive, preserve its source URLs, local ordinals, Notion page IDs, and publication ledger. Its verified historical ordering is #1–#59 followed by #END at library ordinal 60. This is a Civilization snapshot, not a rule for other collections. The generic auditor accepts that legacy inventory without rewriting the library. New extraction commands require a private course profile; see [course profiles](references/courses.md).

Publishing now produces Notion pages only. Existing Obsidian notes remain untouched. For a requested export, use [notion-to-obsidian](../notion-to-obsidian/SKILL.md); for a requested connection pass, use [notion-analyze-and-link](../notion-analyze-and-link/SKILL.md) or [obsidian-analyze-and-link](../obsidian-analyze-and-link/SKILL.md). Legacy converter and stylesheet paths remain available for existing private scripts.
