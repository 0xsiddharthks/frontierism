# Batch coordination and Notion publishing

## Course structure

This workflow publishes to Notion. For an individual lecture, reuse an existing course's schema and guides and verify only the requested page plus any navigation actually changed. Course-wide completion checks apply when a course import is requested. An Obsidian export or cross-page analysis is a separate requested workflow.

Bind the selected course to its private profile before any write; read [courses.md](courses.md). Each course has its own Notion root and lecture parent. A root for another course is never a fallback. Run the profile isolation check across all existing courses, then verify the destination hierarchy live.

Fetch the intended destination before writing; a shared Notion link may identify a database rather than a regular page. Preserve existing user content. Use a database for native properties and the list views specified below. Separate the user's learning progress from the agent's publication status. Use controlled tag names across the course while allowing a genuinely new theme when it helps discovery.

Confirm the database's actual schema before sending property values. Notion page parents and database/data-source parents are not interchangeable; discover the active connector's supported model. Use the connector for supported settings and the built-in browser for remaining view or appearance controls. If neither can complete a setting, record that exact limitation; a numbered index can be a temporary fallback, but it is not a configured native list view.

The destination should offer a clear start point, the full lecture collection, and a future-agent guide. A database can use a Kind property to distinguish Guide rows from Lecture rows. The guide should explain:

- Source hierarchy: the community-maintained lecture article supplies edited transcript and figures; a matching video is optional context unless the task says otherwise. Do not describe the article as the official or complete video transcript without evidence.
- How the course inventory was established, and the ordered source identities and retrieval-time count, including gaps or special labels.
- How to find the manifest, source snapshots, hashes, drafts, validation reports, and publication ledger in the private artifact location.
- What tags and statuses mean, how to change the schema without fragmenting it, and how to preserve user annotations.
- How to re-extract one changed source, compare hashes, review affected material, update the same Notion page, and verify the update.
- Known source gaps, rights limits, and the distinction between a complete source review and a comprehensive historical fact-check.

Do not copy credentials or public-repository-prohibited details into the guide. A private artifact path may be useful in a private Notion guide, but it is not a downloadable attachment. Do not present a local path as a working Notion file link.

## Database properties

For a new course, create the following schema. For an existing course, map to its fetched property names and types; do not create duplicate aliases or reset learner values. A single-lecture request reuses the existing schema and views. Apply these defaults when setting up a course, not as permission to redesign an existing library during an unrelated content refresh.

| Property | Native type | Meaning and initial value |
| --- | --- | --- |
| Name | Title | Printed source label and readable title. |
| Lecture | Number | Stable local course ordinal; preserve meaningful source labels in the title and ledger. |
| Kind | Select | Lecture and Guide, plus source-backed kinds such as Discussion, Exam, Meeting, Bonus, or Session when needed. |
| Topics | Multi-select | A few useful tags from the course's shared vocabulary. |
| Reading | Select | To read, Reading, Review, Confident. New course items start at To read; the learner owns subsequent changes. |
| Review on | Date | Optional learner-chosen review date; leave empty initially. |
| Source | URL | Canonical article URL. |
| Video | URL | Verified matching video, otherwise empty. |
| Published | Date | Actual source publication date, if known. |
| Prepared | Date | When the study note was prepared. |
| Source words | Number | Extracted article word count. |
| Figures | Number | Extracted article figure count; zero is a valid value. |
| QA | Select | Draft, Source checked, Verified in Notion, Needs attention. This tracks production checks, not learning progress. |

Add `Era and region` as rich text only when useful for that course, or choose another clearly useful course-specific context field. Keep unavailable source fields empty, including on guides. Do not copy local-only export fields such as aliases, CSS classes, or a Notion self-link into the reading schema. Do not invent dates or progress to populate a view.

Keep one introduction and one maintenance guide with `Kind = Guide`. Give them deliberate positions in Course order without renumbering source items; keep their identities separate from lecture ordinals in the ledger. Reuse them on later imports.

## Page property layout

Configure the database page layout once so every new lecture inherits it. Pin `Reading`, `Topics`, and `Review on` beneath the title, with readable labels. Put the remaining properties in the details sidebar, using these sections and order:

- **Course context:** Lecture, Kind, and any relevant course-specific context field.
- **Original source:** Source, Video, Published, Figures, Source words.
- **Library record:** Prepared, QA.

Hide empty values in the details sections, preserving meaningful zero counts. Do not repeat pinned properties or the title in the sidebar. Hide decorative property icons where supported. The page body should still begin with the executive recap; do not insert another metadata table or repeat all properties in prose.

Inspect the current layout before an update: an API may replace the entire layout rather than merge it. Preserve the title, content/editor, discussion controls, existing cover handling, and unrelated user choices. Do not add a cover merely because the layout includes a cover slot. Use actual fetched property names and omit optional fields that do not exist. If native layout controls are unavailable, keep the same compact property order in the page's supported property panel and report the limitation.

## Hub list views

All six default views use Notion's native **List** layout, including grouped views. Use a table view only when the user explicitly requests one. Put Course order first and make it the default entry point. Keep full titles readable; a hub row is for choosing what to read, while the page details hold fuller metadata.

| View | Visible properties, in order | Membership and grouping | Sorting |
| --- | --- | --- | --- |
| Course order | Name, Reading | Every course item and both guides; no active filter. | Lecture ascending. |
| By topic | Name, Reading | Exclude Guide; group by Topics. | Lecture ascending within groups. |
| Reading progress | Name, Review on | Exclude Guide; group by Reading. | Lecture ascending within groups. |
| Review queue | Name, Review on, Reading | Exclude Guide AND (Reading is Review OR Review on is on/before today). | Review on ascending, then Lecture ascending. |
| Guides | Name | Kind is Guide. | Lecture ascending. |
| Details | Name, Published, QA | Exclude Guide; add Kind after Name only when distinguishing exams or other item kinds is useful. | Lecture ascending. |

Exclude guides by kind rather than filtering to Lecture: exams, discussions, and other course items still belong in the study views. Use a dynamic today filter so the review queue remains useful; no date means the item enters only through Reading = Review. An empty review queue is valid. Multi-topic items can appear in more than one topic group, so group totals are not unique course counts.

Expose quick filters for Topics, Reading, and Kind in Course order; Topics and Reading in By topic and Details; and Topics in Reading progress. Leave quick filters unset by default. Hide page icons in every list view and use **Full page** when opening an item. These are separate from removing the page's own icon. Keep the default view order as shown above.

Read the active connector's view and layout documentation before supplying configuration. If available, its `notion://docs/view-dsl-spec` and `notion://docs/database-page-layouts` references describe the supported model. Create new views as List directly. A connector may configure properties and filters without supporting a change to an existing view's type; use the browser for that operation instead of guessing parameters. Changing a view's type may reset its settings, so reapply and fetch the intended filters, grouping, sorting, and property visibility afterward. Do not apply table-only column or cell settings to list views.

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

For a new course or requested hub redesign, also verify the setup independently of lecture content:

- Fetch the saved database schema, page layout, and each view. Check native property types, the three pinned fields, grouped details, all six List view types, visible property order, filters, grouping, and sorts. View names alone do not prove their configuration.
- Compare unique page identities in Course order with the source inventory plus both guides. Study views exclude guides and retain all intended item kinds; Guides contains the two guide pages. Evaluate Review queue membership against the saved reading statuses and dates.
- Confirm no native icons on the course root, guides, or published lecture pages. An omitted icon field in a response is not evidence of removal; use explicit empty/null state or inspect the native setting. Check row-icon visibility and Full page opening in the UI if the connector cannot report them.
- Open representative long-title rows, a grouped list, a lecture's property panel, and a guide. Check title readability, Mono font, compact headers, embeds, and folded recall answers. Keep the fetched setup and actual visual-check scope beside the private publication ledger.

The bundled draft and course validators do not verify saved Notion view types, layout, fonts, or icon visibility. Complete the live checks above before claiming that the reading setup is finished. For an individual lecture added to an existing course, check its inherited layout and appearance without recreating all views.

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

Omit native page icons on new course roots, study pages, and both guides. Do not prepend decorative emoji to titles as a substitute. If a template supplies an icon, clear it through a supported property update and verify the result. Removing a page icon and hiding generic icons in list rows are separate checks. Preserve existing page appearance during unrelated content refreshes; change it when the user requests a layout update.

Use Notion's native Mono page font for new study pages and both guides, matching the established library. Check connector support; where font settings are absent, use the page menu through the supported browser. Verify the rendered setting. Database indexes may not expose font controls. Do not simulate a font by turning prose into code blocks or rewriting all rich text. Preserve an existing page's font during unrelated updates.
