# Course profiles, discovery, and isolation

Use a private `course.json` per collection. This is configuration, not permission to publish. Resolve the requested collection from its actual archive and playlist titles; informal names such as “secret societies” or “geopolitics” need source verification rather than a guessed slug. The [site's topics](https://predictivehistory.com/) currently provide entry points such as [Civilization](https://predictivehistory.com/tag/civilization/), [Secret History](https://predictivehistory.com/tag/secret-history/), [Geo-Strategy](https://predictivehistory.com/tag/geo-strategy/), and [Game Theory](https://predictivehistory.com/tag/game-theory/). Treat this as discovery guidance, not a frozen catalog or a promise that all collections have ended.

## Private profile

Example for a future Game Theory run; replace destination placeholders from the user's actual choices and fetched schema. Omit `destinations` for extraction-only work. Do not save filled profiles in this public repository.

```json
{
  "schema_version": 1,
  "course_id": "game-theory",
  "title": "Game Theory",
  "index_url": "https://predictivehistory.com/tag/game-theory/",
  "title_prefix": "Game Theory",
  "destinations": {
    "notion": {
      "root_id": "actual-course-root-id",
      "lecture_parent_id": "actual-course-data-source-id",
      "font": "mono"
    }
  }
}
```

Optional `playlist_url` records a verified matching YouTube playlist. Optional `order` is a complete ordered list of article URLs for unnumbered collections, split parts, duplicates, or noncontiguous source numbers. It must cover exactly the discovered archive; don't silently omit bonus sessions. Store the reason for an explicit order beside it as `ordering_note`. Preserve every title and printed source label independently of its local sorting ordinal. A new series need not use era/region properties; choose subject-appropriate metadata.

`course_id` is stable. The durable item identity is `(course_id, canonical source URL)`, reconciled with its requested URL when redirects change. `lecture_number` remains the machine field for the local ordinal so existing tooling stays compatible; it is not necessarily the printed episode number or playlist position. Titles should retain meaningful source labels such as `END`, `Bonus`, or split-part names.

Private layout:

```text
<private-library>/game-theory/
  course.json
  inventory.json                 # complete paginated source list, even for a partial run
  manifest.json                  # extracted subset, hashes, failures
  publication-ledger.json        # exact source -> Notion page mapping
  01/source.json, notes.json, ...
```

Use separate private archive directories for other courses. Each Notion course has its own root and its own lecture database/data source. Put both guides inside that course root. Record the actual lecture parent separately from the root when they differ. Inspect the hierarchy with the connector before writing. A single lecture in an existing course reuses these bindings and guides.

Validate all known private course profiles together before publishing:

```sh
python3 scripts/course_config.py /private/library/*/course.json
# Require Notion for the selected course:
python3 scripts/course_config.py /private/library/game-theory/course.json --destinations notion
```

The checker rejects duplicate course IDs and shared Notion roots/parents. It also retains validation of legacy optional Obsidian bindings and overlapping folders so old profiles remain usable; those fields never initiate an export. New Obsidian mappings belong to the separate notion-to-obsidian export manifest. Do not remove old bindings merely to adopt this workflow: the archive identity check deliberately protects them from silent changes.

The checker cannot infer remote Notion ancestry; the coordinator verifies that from live reads. Registry scope must include other existing courses, not just the new one. Never use a missing destination as permission to write into a different course. Extraction and drafting can proceed while a required destination is unresolved.

## Discover and extract

```sh
python3 scripts/extract_sources.py --course /private/library/game-theory/course.json \
  --output /private/library/game-theory --inventory-only
python3 scripts/extract_sources.py --course /private/library/game-theory/course.json \
  --output /private/library/game-theory --download-images
# A subset, using library ordinals from the verified inventory:
python3 scripts/extract_sources.py --course /private/library/game-theory/course.json \
  --output /private/library/game-theory --lecture 1 --lecture 2
```

The helper follows public Ghost `rel=next` links, inventories every card, checks the advertised count when present, and stores the retrieved pages as evidence. Default ordering accepts contiguous numeric labels from 1 followed by an optional `END`, with or without `#`; counts are discovered. It fails on unresolved gaps, variants, and unnumbered titles so the coordinator can inspect them and supply `order`. A tag's count is a retrieval-time snapshot, not proof the series has finished. If the site changes markup, exposes different pagination, or only loads through the browser, finish discovery through supported browser controls and create a reviewed compatible inventory; do not fabricate pages or infer completeness from the first screen.

`--refresh` fetches new index/source snapshots. Existing URL-to-ordinal mappings cannot be silently removed or renumbered, including when an old final `END` would move. Review redirects, additions, and changed ordering as an explicit migration, preserve a backup and page IDs, and update the private ledger. Ordinary appended numeric episodes retain their prior ordinals. Never force a refresh by deleting identity checks.

For YouTube, use available metadata/transcript tools or `yt-dlp` if installed. Match by printed number, title, and subject; record unavailable entries, fixes, extras, and unmatched articles. Choose a corrected video variant explicitly. Do not infer episode identity from playlist position or claim video/audio review from metadata. If only a playlist is provided, discover its matching article collection first. If an article is absent, use an authorized available transcript source and record the source type; the bundled HTML extractor does not download video or extract YouTube transcripts. Do not pass a video-only source through the HTML validator with invented article fields.

## Resume and migration

Read the course profile, complete inventory, and per-item ledger before assigning workers. A subset extraction retains the complete expected inventory, and final course audits fail for missing items. Scope worker assignments by course ID and exact source URL as well as ordinal.

The old `civilization-lecture` entrypoint and helper paths forward to this skill. Existing Civilization source/draft records and its old inventory remain readable. No existing Notion pages or vault notes need to move. For a future extraction refresh, first prepare a Civilization profile using the existing index and destinations, then review `--refresh`; source records with `course_id` require that identity and the original `source_label` in their updated drafts. Changing a destination requires a deliberate migration, not a routine refresh.
