# Notion CLI alongside the browser

The `ntn` CLI can make complete readbacks and supported targeted changes easier to inspect and reproduce. Keep the built-in in-app browser first for interactive inspection and native appearance settings. A CLI response cannot prove how a page renders.

This workflow was exercised with `ntn 0.23.21`: a bounded 87-page export, a complete data-source query, and one exact Markdown insertion followed by full content and metadata comparison. Commands and schemas can change; inspect the installed version and live endpoint schema before relying on this syntax elsewhere.

## Check the existing session

```sh
command -v ntn
ntn --version
ntn --help
ntn whoami
ntn pages get --help
ntn datasources query --help
ntn api --help
```

Use the existing authenticated account when it is appropriate to the requested destination. If sign-in is needed and authorized, follow the installed CLI's documented login flow. Do not inspect credential stores or print tokens to diagnose ordinary access. Keep identity output, page IDs, payloads, and exports outside the public repository. Do not add account-specific environment defaults to the skill.

## Complete exports

```sh
ntn pages get "$reading_page_id" --json > /private/run/page.json
```

In the tested version, JSON contains both `page` metadata and a `markdown` object. Check both returned IDs against the requested ID. Require `markdown.truncated` to be exactly `false`, `markdown.unknown_block_ids` to be an empty array, and `markdown.markdown` to contain the expected text. Missing completeness flags are an unresolved check, not success. Check the page's parent, properties, icon, and archive/Trash state separately.

For a bounded collection, make a private JSON array of the exact expected page UUID strings. From this skill directory, run:

```sh
python3 scripts/notion_cli_readback.py \
  --pages-file /private/run/page-ids.json \
  --output /private/run/readback-01
```

Alternatively, repeat `--page-id UUID` for a small explicit set. The helper uses a new or empty output directory, limits concurrency, paces request starts, saves full exports privately, and fails when any page needs attention. It neither discovers an unbounded workspace nor writes to Notion. A transient failure requires inspection and a new bounded run; it does not silently retry writes or declare partial coverage complete.

Compare every exported body with its intended content, allowing only understood serialization differences, such as equivalent native mention markup or whitespace. Compare metadata by property type. Matching counts or lengths alone cannot establish fidelity. Retain folded answers, native links, notes, and source keys. Export completeness does not establish that a source was read or that its interpretation is sound.

## Collection queries

```sh
ntn datasources query "$reading_data_source_id" \
  --limit 100 --sort 'Number asc' --json > /private/run/rows.json
```

Confirm these options with current help. Do not rely on the default page size or assume `--limit` returns the whole collection. Inspect `has_more` and `next_cursor`, follow the installed command's pagination interface when necessary, and verify the exact expected ordinals, unique source URLs, unique page IDs, and guide count. Keep production QA separate from the learner's Reading and Review on fields.

## Targeted edits

Fetch the current page immediately before an edit. Compare it with the last readback and preserve concurrent learner changes. The tested CLI's `pages edit` replaces the entire page body; do not use it as a casual insertion command. Frontmatter is not a general property-update mechanism: the tested create/edit commands strip it, with only a create-time title applied.

Inspect current official endpoint documentation and schema through the CLI:

```sh
ntn api -X PATCH "v1/pages/$reading_page_id/markdown" --spec
ntn api -X PATCH "v1/pages/$reading_page_id/markdown" --docs
```

The tested endpoint supports a structured exact-match update. Save a request like this in a private JSON file; replace the sample passage with text observed exactly once in the fresh page:

```json
{
  "type": "update_content",
  "update_content": {
    "content_updates": [
      {
        "old_str": "## Maintenance and reuse",
        "new_str": "## Workflow notes\nA new, reviewed paragraph.\n## Maintenance and reuse",
        "replace_all_matches": false
      }
    ],
    "allow_deleting_content": false
  },
  "allow_async": false,
  "markdown_version": "v1"
}
```

```sh
ntn api -X PATCH "v1/pages/$reading_page_id/markdown" \
  --data @/private/run/update.json > /private/run/update-result.json
ntn pages get "$reading_page_id" --json > /private/run/after.json
```

Inspect warnings and operation results. A batch can partially apply when some matches fail; an exit status alone is insufficient. Compare the complete new body against the complete intended body and confirm unrelated metadata is unchanged. If the outcome is ambiguous, fetch and reconcile before retrying. `allow_async: false` avoids accepting a queued operation as a finished edit; if an endpoint still returns a job, inspect its documented completion state.

Use the documented page-properties endpoint for property changes and fetch the stored value afterward. Do not assume an accompanying property field on a content operation was applied. Keep page appearance changes in the browser unless the installed API explicitly documents them; the tested public page-update schema did not expose the native font setting.
