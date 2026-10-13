# Export mappings and fidelity

## Private manifest

Store the manifest, full Notion snapshots, prior exported Markdown, backups, and checksums outside the active vault and public repository. Each page record needs its stable Notion page ID and URL, source revision, parent identity, destination path, prior exported hash/content, and written hash. Each asset record needs its source block/attachment identity, source URL, local path, media type, byte length, and checksum. Do not put temporary signed URLs or credentials into public files.

For Predictive History, an existing course ledger can seed identity and destination lookup, but fetch the current Notion content. An old `destinations.obsidian` profile entry is useful context, not permission to refresh that folder. Keep the export manifest separate from the publisher's source-to-Notion ledger.

Plan all paths first. Sanitize filenames, check for empty names, existing-file collisions, Unicode/case equivalence, and paths escaping the destination through `..` or symlinks. For duplicate titles, retain meaningful hierarchy or add a short stable page-ID suffix. Preserve established paths on re-export unless a rename is requested; a rename must update incoming links in the authorized scope. Export source pages once even if several views display them.

Use flat YAML properties with safely quoted strings. Useful generic properties are `notion_page_id`, `notion_url`, `notion_edited_at`, and `exported_at`, plus the source's meaningful tags, status, dates, and aliases. Preserve property types where possible and document lossy mappings. Relations become links to mapped notes or retained Notion references. Formulas and rollups are timestamped values, not recreated live calculations. Child pages are separate notes with navigation; database views need an explicit local representation, not an empty dropped block.

## Rendering

- Preserve headings, prose, lists, tables, equations, code languages and literal code contents. Do not reinterpret link syntax inside code examples. Table spans, rich nested cells, arbitrary embeds, synced blocks, and unusual block types require inspection instead of silent flattening. Expand synced content only through a complete authorized read; record unavailable content.
- The bundled converter supports simple rectangular HTML tables, page mentions, Markdown images, file blocks, details, callouts, and columns in Notion's enhanced-Markdown format. It is not a parser for every connector format. Normalize a connector's response deliberately and check the result against its original blocks. Its strict failure is a review checkpoint, not permission to discard that content.
- Download permitted media through the connector or actual attachment URL. Refresh expired Notion URLs through a new fetch; never claim a remote signed URL is an offline embed. Prefer an existing verified source file when it is the same asset. Deduplicate asset bytes by checksum, while preserving distinct captions and intentional placement. For a missing image, retain a clear unavailable marker and report it.
- Images, PDFs, and supported media use `![[hub/_assets/name.ext]]`. Show the caption beside the embed without another download-link list. Render JSON/text attachments through a Markdown wrapper containing the actual content in a correctly sized code fence; embed the wrapper section once, usually collapsed. Retain a machine-readable original privately or beside the wrapper when useful. For unsupported binary formats, one descriptive attachment link is an honest fallback; do not fabricate an embed or duplicate it.
- In-scope page references become qualified wikilinks. Out-of-scope references remain working Notion links and must not expand the export recursively. Preserve useful labels. A Notion block link needs a verified heading/block-anchor map; do not translate a block UUID into an invented Obsidian heading.
- Separate adjacent callouts with a blank line, including a quote-level separator for nested siblings. Fold recall answers independently. Keep long tables and detailed charts full width. Pair simple figures only when that improves reading.

For the helper, `pages` maps compact page IDs to local targets; `images` and `files` map original URLs/URIs to archived local targets. `external_pages` explicitly maps verified out-of-scope references to their Notion URLs. `file_labels` supplies attachment-specific callout titles; pass `attachment_label='Attachment'` for generic notes (the legacy default remains `Source record`). Block-anchor links require a reviewed adapter or an explicit external mapping; unsupported hover-title links fail for review rather than losing information.

The optional [assets/obsidian.css](../assets/obsidian.css) styles gallery and figure callouts under `cssclasses: [notion-export]` and retains existing Predictive History/Civilization classes. Install it only when useful for the requested export; preserve the enabled snippets and all unrelated appearance settings. Reload and verify the snippet in Obsidian when installed. Native content must remain readable without the snippet or community plugins.

For a hub, use a start note and links to members. A `.base` may provide sortable properties and review views, with filters restricted to this export's folder and identity. Verify current syntax with the [official Bases reference](https://help.obsidian.md/bases/syntax) when creating one, then inspect its rendered count. Never mix unrelated courses that happen to share a lecture ordinal.

## Repeat export

Compare the prior generated Markdown with the current local file and freshly converted Notion content. If the local file is unchanged, replace it with the new verified export. If Notion is unchanged but local content differs, retain the local file. When both changed, merge only demonstrably nonoverlapping edits; keep user annotations, Obsidian-only keyword links, and analysis. Stage ambiguous conflicts separately and report the exact affected files. Do not mark a conflicted file synchronized or replace the prior baseline with the unmerged remote version.

Re-read the destination immediately before each write to catch edits made during staging. Write through a temporary sibling file and atomic replacement when practical, then verify bytes. A missing source page may be deleted, moved, filtered, or inaccessible: retain its local copy until deletion is explicitly requested. Do not propagate local edits back to Notion through this exporter.

Useful official references when implementing a new conversion: [links](https://help.obsidian.md/links), [embeds](https://help.obsidian.md/embeds), [properties](https://help.obsidian.md/properties), and [callouts](https://help.obsidian.md/callouts).
