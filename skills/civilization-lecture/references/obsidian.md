# Obsidian migration and course connections

## Prepare and preserve

Confirm the exact vault path from the user or Obsidian's vault registry. Inventory the destination and make a dated backup outside the active vault. Verify file counts and hashes before removing or moving anything. Only clear existing notes when the user has requested that cleanup; prefer a recoverable archive. Preserve `.obsidian` preferences and plugins unless the requested setup needs a specific change. Never treat a fresh export as permission to overwrite later user edits.

Fetch current Notion pages before exporting. Preserve their personal notes, reading status, and review dates. Record a private lecture-number-to-page-ID-to-vault-path manifest. Build in a staging directory, validate it, then copy and verify the destination. Do not save private paths or page identifiers in this public skill.

## Native formats

- Use numbered Markdown files and flat YAML properties for lecture, tags, reading, review date, source, and matched video. Quote strings safely. Register empty review fields as dates when needed.
- Convert internal page mentions into `[[vault/path|Readable name]]` links. Use stable aliases and unique paths; avoid ambiguity between source records and lecture notes.
- Copy each inspected image locally with a unique name, verify its checksum, and use `![[path/image.webp]]`. Put the description immediately beneath it. No second hyperlink list.
- Convert Notion details into native foldable callouts. Use collapsed answer cues so recall remains useful. Convert supported tables without losing cells; stop and review spanning or unusual tables.
- A JSON file is not a natively rendered Obsidian document. For an embedded source record, use a Markdown wrapper containing its actual JSON in a fenced block, and embed that section once inside a collapsed callout. A raw JSON companion may be retained for tools without another reader-facing link.
- The optional [obsidian.css](obsidian.css) snippet styles native gallery/figure callouts into responsive pairs. Keep maps and detailed charts full width. All content remains readable without the snippet or community plugins.
- A native `.base` can provide sortable course and review views. Verify its current syntax against official documentation and check the actual result count in Obsidian. Keep a simple navigation route available when a base is not supported.

`scripts/export_obsidian.py` supplies `frontmatter`, `filename`, `convert`, and `validate_wikilinks`. The converter accepts explicit page, image, and file maps and rejects unmapped references. It handles the subset used by these study pages, not arbitrary Notion documents. It does not perform vault cleanup or synchronization. Import it from a private orchestration script; pass the completely fetched body, archived image paths, and local attachment wrappers.

## Cross-link review

Create the initial lecture notes before the cross-linking pass when the user requests that order. When parallel agents are authorized, assign disjoint source ranges and use one coordinator for applying edits. Each reviewer scans the whole course's recaps, reads their assigned notes fully, and reads every proposed destination fully.

Prefer a small set of strong connections per page, usually three: a contrasting explanation, a related mechanism, a methodological comparison, or a later development. Explain why to follow each link with a concise original comparison prompt. Avoid keyword-only links, self-links, repeated destinations, and duplicating previous/next navigation without a useful reason. Do not turn the connection section into more protected-source recap. Record the source and target basis privately for review.

Use native wikilinks in Obsidian and native page mentions in Notion. Links are directional editorial choices; Obsidian backlinks provide the return path. Do not fabricate reciprocal prose merely to make the graph symmetric. An optional course map or focused graph can help navigation without an unreadable all-to-all network.

## Verify

Check every expected lecture number, all local file/link targets, one embed per source image, image hashes, and valid source-record JSON. Compare converted teaching text, tables, citations, and personal notes with the fetched source. Exclude technical source records from a course graph when they would distract from conceptual connections. Verify representative rendered callouts, images, file embeds, tables, links, and base views in Obsidian. Fetch every changed Notion page and compare complete content. Preserve a restoration manifest and report local completion separately from unverified cloud synchronization.

Official syntax: [links](https://help.obsidian.md/links), [embeds](https://help.obsidian.md/embeds), [properties](https://help.obsidian.md/properties), [callouts](https://help.obsidian.md/callouts), and [Bases](https://help.obsidian.md/bases/syntax).
