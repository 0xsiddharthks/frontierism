# Private draft and verification records

Store run artifacts outside a public repository. The extraction script produces a course `manifest.json` and one directory per lecture containing `source.json`, `article.md`, `article.txt`, `article.html`, `original.html`, and any downloaded `figures/`. For a new course archive:

```sh
python3 scripts/extract_sources.py --output /private/path/civilization-study --download-images
```

Add `--lecture 12` to select one lecture; repeat it for a subset. Use `--refresh` only when a new source snapshot is wanted. Source #END has library ordinal 60; preserve the source's END label rather than implying that the article itself prints #60.

## notes.json

The following is an illustrative shape, not source content. Unknown run-specific values must be filled from the actual source and Notion schema. Extra fields are allowed for useful teaching or audit evidence.

```json
{
  "schema_version": 1,
  "lecture_number": 12,
  "title": "12 · Actual lecture title",
  "source_url": "https://predictivehistory.com/actual-article/",
  "source_sha256": "the actual hashes.article_text_sha256 value",
  "properties": {
    "Name": "12 · Actual lecture title",
    "Lecture": 12,
    "Kind": "Lecture",
    "Topics": ["A shared topic"],
    "Era and region": "A useful period and geographic description",
    "Reading": "To read",
    "Source": "https://predictivehistory.com/actual-article/",
    "Video": "https://www.youtube.com/watch?v=actual-id",
    "date:Published:start": "2025-01-01",
    "date:Prepared:start": "2026-01-01",
    "Source words": 4000,
    "Figures": 1,
    "QA": "Draft"
  },
  "content": "Complete page body as the connected Notion tool's Markdown dialect",
  "coverage": {
    "read_source_ids": ["heading-001", "paragraph-001", "figure-001"]
  },
  "figures": [
    {
      "source_id": "figure-001",
      "status": "inspected",
      "disposition": "linked",
      "note": "What was actually checked and why this disposition is useful"
    }
  ],
  "audit": {
    "full_source_read": true,
    "semantic_reviewed": true,
    "source_derived_words": 180,
    "quoted_words": 0,
    "rights_basis": "protected-web-default",
    "draft_ready": true,
    "limitations": []
  }
}
```

Property names and allowed options must match the actual database, not an assumed schema. The validator accepts `Source URL`/`Video URL` as aliases if that is how the destination names them. `Video` can be omitted if not established. Use the source publication date from metadata; never use the retrieval date as publication date. Omit unavailable dates rather than inventing them. `QA` describes production review; `Reading` belongs to the learner.

### Source identity and coverage

- `source_sha256` copies `source.hashes.article_text_sha256`, the SHA-256 of the extracted article text. The on-disk `article.txt` adds one final newline after the hashed text.
- `coverage.read_source_ids` contains every `source.blocks[*].id` exactly once, recorded after actual reading. These IDs address the private `article.md` anchors. They are not public webpage fragment identifiers unless the page itself supplies them.
- Optional `anchors` records can map a claim or page section to source block IDs: `{"label":"Executive recap","source_ids":["paragraph-001"]}`. Use these to make fidelity review reproducible; they must refer to real source blocks.
- `figures` contains exactly one record for every `source.figures[*].id`. `status` is `inspected`, `unavailable`, `duplicate`, or `decorative`; `disposition` is `linked`, `embedded`, or `omitted`. Every record needs a meaningful `note`. Explain any unavailable or omitted figure in `audit.limitations` when it affects the learner.
- Full block coverage includes source tables and mathematics. Their presence does not imply accurate reproduction; the semantic reviewer checks they were understood and given suitable treatment.
- `audit.semantic_reviewed` attests to fidelity, conceptual usefulness, source attribution, and visual honesty. It is an agent/human judgment, not an outcome a structural script can establish.

### Rights and source budgets

`audit.source_derived_words` accounts for all content derived from the lecture webpage, not just the executive recap. `quoted_words` is a subset. Default caps are 200 derived words and 25 quoted words. These are conservative workflow defaults; obey a lower active tool/source limit. Store a lower limit as `source_word_limit` or `source_quote_limit`.

For a different verified rights basis, use an accurate `rights_basis` and nonempty `rights_evidence`; set numeric limits if appropriate. A higher limit without a documented basis fails validation. Do not use a high number as a substitute for deciding what the rights permit.

Other sources can be tracked in `audit.source_budgets`, each as `{"url":"https://...","derived_words":70,"quoted_words":0,"word_limit":200,"quote_limit":25,"rights_basis":"protected-web-default"}`. Cite those sources near the claims they support. Numbers alone do not prove compliance: the semantic reviewer must check what the prose is derived from.

If extraction has warnings, investigate them. Resolved or bounded warnings can be listed verbatim in `audit.source_warnings_reviewed`, with their actual implications explained in `limitations`. A paywall, incomplete extraction, or broken text reconstruction cannot pass as complete source review.

## Validate a draft

Run from the skill directory, or use an absolute script path:

```sh
python3 scripts/validate_notes.py \
  --source /private/path/civilization-study/12/source.json \
  --notes /private/path/civilization-study/12/notes.json \
  --report /private/path/civilization-study/12/validation.json
```

The command emits JSON and returns nonzero on failure. `--allow-draft` permits `draft_ready:false` during authoring; missing coverage and bad identity remain failures. `--require-published` also requires the separate complete readback record described below. Never satisfy a failing check by merely changing an audit boolean: do the underlying work.

## publication and readback

After a successful creation, save `notes.publication` with `page_id` and `parent_id` (the actual database/data-source or page identity used by the tool). Keep these private. Persisting the response prevents accidental duplicates after interruption.

Save the actual full fetch response privately, then normalize its body and properties into `readback.json`. A typical record is:

```json
{
  "page_id": "actual-created-page-id",
  "parent_id": "actual-destination-id",
  "lecture_number": 12,
  "complete": true,
  "truncated": false,
  "errors": [],
  "unknown_block_count": 0,
  "properties": {},
  "content": "The complete fetched page body, without outer API metadata",
  "checked_at": "2026-01-01T12:00:00Z",
  "verification": {
    "links_valid": true,
    "rendering_reviewed": true
  }
}
```

`properties` contains the normalized values actually fetched, not values copied from the draft. The validator compares required properties and body text. Equivalent whitespace is normalized. If the connector changes markup without changing meaning, the reviewer may add `verification.content_equivalent:true` and `content_equivalence_note` explaining the checked serialization difference. This is an explicit reviewed exception, not a blanket mismatch bypass. Keep the raw readback available for inspection.

Run the same command with `--readback /private/path/.../readback.json --require-published`. All reads must be complete, no output truncated, all error arrays empty, unknown block count zero, and the recorded parent/page identities must match. Additional navigation or metadata added after publication needs a fresh draft record and readback.
