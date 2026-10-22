# Publishing and verifying source analysis

## Destination and identity

These instructions apply only to direct publication or an explicitly assigned publication phase. Draft-only source workers return private artifacts without Notion writes. For a direct source request, use [notion-library.md](notion-library.md) unless a destination is supplied. A collection coordinator supplies its destination, live schema, source/page mapping, and publication constraints. Preserve existing field names and learner customizations; do not apply a second schema to the database.

Read the connector's current enhanced Markdown and relevant view/page-layout documentation before using those capabilities. Normalize source identity, edition, and scope and enumerate paginated matches before creating. Keep a private record of snapshot/version, reading coverage, draft, destination, page ID, and readbacks. On an ambiguous creation result, query the destination before retrying. Wait for asynchronous completion before dependent changes.

## Reading experience

Try the built-in in-app browser first when available for interactive inspection and native settings. Inspect the supplied example and actual saved collection. Connectors and the [CLI](notion-cli.md) can handle supported structured changes and readbacks; they do not establish visual appearance. Use a separate background tab if repetitive work would interrupt the user's reading.

Use native **List** views for hubs and collections, with few useful properties beside each title. New analysis pages and guides omit page icons. Keep detailed metadata in page details and the summary at the start of the body. Follow the chosen destination profile for visible properties and grouping; do not force corpus ordinals or audiovisual fields onto unrelated sources. Preserve existing user customizations during refreshes.

Verify native row-icon visibility, full-page opening, and the chosen font when these are part of the requested setup. Wait for the destination title and identity before using appearance controls: the old page's Actions button can remain visible during navigation. If bare-ID navigation aborts, use an observed native link or full URL. Inspect state after a failed action and retry only after resolving its cause. A repaired in-app browser should be retried rather than permanently replaced by a fallback.

## Safe refreshes

Fetch the current page immediately before editing and compare the affected region with the last reviewed snapshot. Apply targeted changes or reconcile concurrent edits. Preserve learner annotations, comments, Reading, Review on, existing connections, media, page identity, and unrelated content. Do not replace an edited page with a stale draft. A new source extraction can invalidate old block locators; recheck the affected claims against the new snapshot.

Use a documented property-update operation for metadata. Do not assume that a content-edit command applies an accompanying property field. Fetch the stored values afterward. QA/production review and the learner's reading progress are separate concepts; updating tags or layout does not advance a substantive review date.

## Readback and closure

Fetch every changed page completely, including continuation results or paginated children. Require the expected identity and parent, no truncation, and no unresolved unsupported blocks. Compare the complete body and metadata with the intended result, allowing only understood lossless serialization differences. Counts, matching lengths, successful HTTP responses, or valid links alone do not establish fidelity.

Check source links, attribution, folded answers, inspected media, native internal targets, and learner-owned content. Query the destination for the intended source identity and duplicate URLs/editions. The collection coordinator separately audits membership, unique page mappings, guide count, and navigation. Retain pre-edit snapshots and update the private ledger to the verified current page so future audits do not mistake an approved change for drift.

Fetch saved schema, layout, and view configuration independently of page bodies. Check List type, visible properties, grouping, filters, and sorts where configured. Inspect representative pages, long titles, toggles, grouped lists, and consequential images in the in-app browser. Report the scope accurately: all-page content verification is different from visually inspecting every page, and structural checks do not prove the interpretation sound.

Set production QA only after its defined checks pass; keep factual verification claims proportional to the actual evidence checked. If a write remains unavailable after inspection and a bounded retry, preserve the analysis outside the public repository and report it as unpublished. Do not change sharing permissions or contact others.
