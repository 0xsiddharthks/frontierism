---
name: obsidian-analyze-and-link
description: Analyze an existing Obsidian note collection and add reviewed connections, sparse inline concept wikilinks, or requested synthesis. Use for a local post-analysis pass within a chosen vault folder or explicit note set.
---

# Analyze and link Obsidian notes

Improve the relationships in an existing local collection, using native wikilinks and backlinks. Work on the chosen Obsidian notes as they currently exist; do not import a newer Notion copy first or write these changes back to Notion. For a requested export, use [notion-to-obsidian](../notion-to-obsidian/SKILL.md); for analysis maintained in Notion, use [notion-analyze-and-link](../notion-analyze-and-link/SKILL.md).

## Read the bounded collection

Resolve the exact vault and selected folder or note set. Inventory notes and existing links, including aliases and relevant headings. Exclude attachments, raw source wrappers, generated indexes, and templates from conceptual targets unless their content is specifically relevant. Never infer membership from a lecture number shared by different courses.

Use the shared [review method](../notion-analyze-and-link/references/review-method.md) for candidate selection, complete source/target reads, meaningful comparison, and private evidence records. Only that analytical method is shared; all changes in this workflow are local. Scan the selected collection and read every proposed target fully. Cross-folder/course links require the requested scope to include those collections.

## Write readable connections

Add or refine a concise Connections section, usually a few links with an original explanation of each relationship. Prefer `[[folder/path/Target note|Readable label]]` so duplicate basenames cannot redirect the link. Include heading or block anchors only when they resolve. Keep links directional; Obsidian provides backlinks without invented reciprocal prose. Reconcile existing edges before adding more.

For inline concept links, select meaningful phrases already present and use `[[folder/path/Target note|original words]]`. Preserve the rendered wording and edit only the reviewed occurrence. Avoid automatic global keyword replacement, YAML, code examples, existing links, and personal annotations. A note need not meet a link quota. Keep navigation and embeds separate from the conceptual connections.

When synthesis is requested, place it in the existing hub or a clearly named analysis note within the selected folder, with supporting wikilinks. Explain comparisons and unresolved questions without recasting the author's claims as verified facts. Do not create a concept note for every keyword or an all-to-all graph.

## Preserve and verify

Save dated copies and hashes of the selected files outside the active vault before editing. Stage exact patches and review them. Re-read each file before applying its patch; preserve changes made since the snapshot. Retain frontmatter types, tags, reading progress, citations, media, callout separators, and user notes. Reruns should revise or skip an equivalent connection rather than duplicate the section or wrap an already linked phrase.

Validate all added link targets, case-sensitive spelling, duplicate basenames, aliases, heading/block fragments, and preserved visible text. The shared export helper's `validate_wikilinks` in [notion-to-obsidian](../notion-to-obsidian/scripts/export_obsidian.py) can assist with supported syntax; inspect any constructs outside its coverage in Obsidian. Compare pre/post checks so unrelated pre-existing broken links are reported separately instead of being silently edited.

Inspect representative inline links, connection sections, and backlinks in Obsidian. Open the actual destination, rather than treating a colored link as proof of correctness. Save an applied-change ledger and hashes privately. If these notes have an export manifest, record the analysis as a local overlay with its before/after hashes; preserve the prior remote-generated baseline so a later three-way export can recognize the local additions.

Report the reviewed scope, notes changed, connections and inline links added or revised, and any unresolved conflicts. Notion remains unchanged unless the user separately requests a corresponding Notion analysis pass.
