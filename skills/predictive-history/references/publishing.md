# Batch coordination and Notion publishing

## Course structure

This workflow publishes to Notion. For an individual lecture, reuse an existing course's schema and guides and verify only the requested page plus any navigation actually changed. Course-wide completion checks apply when a course import is requested. An Obsidian export or cross-page analysis is a separate requested workflow.

Bind the selected course to its private profile before any write; read [courses.md](courses.md). Each course has its own Notion root and lecture parent. A root for another course is never a fallback. Run the profile isolation check across all existing courses, then verify the destination hierarchy live.

Fetch the intended destination before writing; a shared Notion link may identify a database rather than a regular page. Preserve existing user content. A database supports a numbered lecture list with sortable properties; useful fields include title, lecture number, source URL, topics, era and region, study status, and source review status. Separate the user's learning progress from the agent's publication status. Use controlled tag names across the course while allowing a genuinely new theme when it helps discovery.

Confirm the database's actual schema before sending property values. Notion page parents and database/data-source parents are not interchangeable; discover the active connector's supported model. If native views cannot be configured by the available tool, a numbered index and theme navigation can still be useful. State the real structure instead of claiming unsupported views were created.

The destination should offer a clear start point, the full lecture collection, and a future-agent guide. A database can use a Kind property to distinguish Guide rows from Lecture rows. The guide should explain:

- Source hierarchy: the community-maintained lecture article supplies edited transcript and figures; a matching video is optional context unless the task says otherwise. Do not describe the article as the official or complete video transcript without evidence.
- How the course inventory was established, and the ordered source identities and retrieval-time count, including gaps or special labels.
- How to find the manifest, source snapshots, hashes, drafts, validation reports, and publication ledger in the private artifact location.
- What tags and statuses mean, how to change the schema without fragmenting it, and how to preserve user annotations.
- How to re-extract one changed source, compare hashes, review affected material, update the same Notion page, and verify the update.
- Known source gaps, rights limits, and the distinction between a complete source review and a comprehensive historical fact-check.

Do not copy credentials or public-repository-prohibited details into the guide. A private artifact path may be useful in a private Notion guide, but it is not a downloadable attachment. Do not present a local path as a working Notion file link.

## Parallel work

The coordinator owns inventory, shared schema, tag conventions, navigation, and the publication ledger. Assign workers explicit course IDs, disjoint source URLs/ordinals, and artifact paths. Workers read full sources, review images, draft notes, run validation, and report exact limitations. They must not alter neighboring drafts or shared metadata without coordination.

Prefer one publishing coordinator when the tool offers no atomic idempotency. If workers publish independently, assign an exclusive lecture/page and a per-lecture ledger record. Never let several workers create the same title opportunistically. Aggregate results by lecture number, not completion order, and verify the entire expected range before reporting course completion.

## Safe creation and refresh

Record `(course_id, canonical source URL)` as the durable identity; retain requested URLs, printed source labels, and stable library ordinals in the ledger. Before creation, check the private publication ledger and read the intended parent/database for an existing match. Page titles alone are weak identities. Do not merge unrelated pages merely because their titles resemble one another.

Prepare the complete local draft and validate it before writing. On a successful creation, immediately persist the returned page ID in a private per-lecture record. On an error, timeout, or unknown response, inspect the destination for the same identity before retrying. Do not blindly retry a creation that may have succeeded.

For an update, fetch the page first. Replace only the agent-managed region or the known content that the user authorized updating. Preserve personal annotations, study progress, comments, reviewed Connections sections, inline links, and unrelated blocks. Reconcile against the last saved readback instead of blindly republishing an older draft. If source changes undermine an existing connection, record it for a targeted review; do not silently drop the section. If new user edits conflict with a proposed rewrite, finish the independent work and surface the concrete conflict instead of deleting their work.

Use bounded, backoff retries for transient reads or idempotent updates. Respect service retry hints. After repeated unchanged failures, retain the validated draft and exact checkpoint; do not create alternate duplicate pages as a workaround.

## Verification

Fetch every written page and all continuation pages/children needed for a complete result. Reject truncated tool output or malformed JSON before parsing. Keep diagnostics separate from machine-readable data. Do not interpret a partial fetch with no visible errors as a clean readback.

Readback checks include:

- Correct unique lecture number, title, source URL, destination parent, and ledger page ID.
- Expected properties, rendered sections, links, and content. Compare normalized text where the connector changes equivalent Markdown formatting; investigate missing semantics rather than requiring byte equality across serializers.
- All source figures have the intended embed/omission treatment, with honest inspection status. Each figure or artifact is displayed once, without a redundant hyperlink list; captions survive any consolidation.
- Previous and next links point to actual neighboring lecture pages, with sensible first/last boundaries.
- No error or unknown/unsupported blocks, unfinished placeholders, accidental prompt text, broken local links presented as public files, or duplicate page creations.

Set publication status to verified only after a complete clean readback. The validator accepts a separate readback record so “draft ready” cannot be confused with “published and verified.” A human/agent must still inspect actual rendering when tool serialization cannot establish it.

For the Notion enhanced-Markdown fetch shape, `scripts/record_readback.py` can normalize a saved full response into the validator's readback record. It compares actual returned content and URLs with the draft, rejects incomplete or unknown blocks, and accepts only narrow lossless escaping changes. Its structure review is not a claim that every page was opened visually; inspect representative rendered pages as well. Link preservation and live destination reachability are distinct checks.

```sh
python3 scripts/record_readback.py --notes /private/path/12/notes.json \
  --fetch /private/path/12/notion-readback.json --output /private/path/12/readback.json
```

For final course integrity, compare the manifest and ledger: exactly one page per expected number, no missing or repeated numbers, unique canonical source URLs, no reused page IDs, and every page verified. A sample of good pages cannot establish that all pages passed.

The course auditor rechecks every stored full fetch against its draft, checks public heading fragments against extracted HTML IDs, and can check neighboring page navigation:

```sh
python3 scripts/audit_course.py --archive /private/library/game-theory \
  --require-published --require-navigation --report /private/path/course-audit.json
```

For navigation checks, store `notes.navigation.previous` and `.next` as actual neighboring page IDs, omitting the absent neighbor at either end. The visible body must contain those targets. Native Notion mentions are preferable to ordinary links for internal navigation.

Record file uploads in `notes.attachments` as the connector returned them, including `filename` and `markdown_source`. The readback helper accepts conversion from that exact upload source to a Notion file-block URI only when the filename matches. This checks that the attachment reference survived; it does not independently download and hash Notion's uploaded bytes.

## Appearance

Use Notion's native Mono page font for new study pages and both guides, matching the established library. Check connector support; where font settings are absent, use the page menu through the supported browser. Verify the rendered setting. Database indexes may not expose font controls. Do not simulate a font by turning prose into code blocks or rewriting all rich text. Preserve an existing page's font during unrelated updates.
