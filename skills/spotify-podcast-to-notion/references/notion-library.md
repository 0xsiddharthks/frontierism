# Notion library conventions

## Find the intended library

The shared skill contains no private workspace IDs. Read the local destination file at:

```text
${XDG_CONFIG_HOME:-$HOME/.config}/spotify-podcast-to-notion/destination.json
```

Its keys are `schema_version` (currently 1), `hub_page_id`, `hub_url`, `database_id`, and `data_source_id`. These identify a destination, not credentials. Keep the file outside the public repository. Fetch the configured hub and database to confirm access and current schema before using them; never assume a stored ID is still valid.

A destination in the user's request wins. If configuration is absent, search Notion for **Podcast Research** and inspect plausible matches. Reuse an unambiguous library intended for this work. If several destinations remain plausible, ask while continuing the analysis. If no library exists and the user requested saving an analysis, create a private **Podcast Research** hub and an **Episodes** database beneath it. Use the connector's private draft creation mode for a new root hub with no named parent. Save the verified destination in the local file after creation. Do not store workspace IDs in this skill or commit the configuration.

Use the data source ID returned by fetching the database for episode pages. A database ID is not a regular parent page ID. When organizing an existing analysis, move its page into the data source instead of copying its body into a new page. Fetch before and after the move to confirm preservation.

## Native properties

These are the library's default fields. Fetch the live schema and respect renamed fields or deliberate customizations. Add missing fields needed for the requested metadata; do not rebuild an existing database or replace its unrelated properties. New select values for real shows, guests, languages, and relevant topics are expected.

| Property | Notion type | Meaning |
| --- | --- | --- |
| Name | Title | Readable analysis title; avoid duplicating the page icon. |
| Episode title | Rich text | Original publisher title, even if sensational or different from the analysis title. |
| Show | Select | Exact show name; reuse its existing option. |
| Host | Rich text | Verified host name(s), not workspace People references. |
| Guests | Multi-select | Verified guest names, one option per person; omit honorifics for consistent filtering. |
| Publisher | Rich text | Organization credited by the source. |
| Published | Date | Episode release date; preserve source precision and note conflicts. |
| Duration (min) | Number | Decimal minutes: milliseconds / 60,000. Keep exact HH:MM:SS in the body. |
| Spotify | URL | Canonical episode URL, without share/tracking parameters. |
| Episode ID | Rich text | Spotify's stable episode ID; primary duplicate key. |
| Publisher page | URL | Verified page for this episode, when available. |
| Tags | Multi-select | Substantive topics, institutions, and places discussed. |
| Format | Select | Video podcast; Audio podcast. Leave empty if unknown. |
| Language | Select | Language actually used in the episode; support additional languages as needed. |
| Chapter count | Number | Chapters in the primary scheme. Zero means confirmed none; missing means unknown. |
| Transcript source | Select | Spotify automatic; Publisher; User supplied; Audio transcription; Unavailable. |
| Coverage | Select | Full transcript; Partial transcript; Episode notes only. |
| Review status | Select | Analyzed; Partial; Needs transcript. |
| Fact-check scope | Select | Targeted checks; Not independently checked. |
| Reviewed | Date | Date the substantive analysis was last reviewed, in the user's timezone. |

`Transcript source` identifies provenance; document whether a publisher/user transcript is automatic or edited in the body. Add an accurate source option rather than mislabeling an editorial Spotify transcript as automatic. `Full transcript` describes text read, not audio verification or permission to reproduce it. State omissions and version differences in the coverage section. Do not mark metadata-only work Analyzed. Updating tags alone should not advance Reviewed.

The connector uses SQLite-style values. Follow the fetched schema and current tool documentation:

- Numbers are numeric, not strings. 65 minutes 34 seconds is about 65.57 minutes, not 65.34.
- Dates use `date:Published:start` and `date:Published:is_datetime` (0 for a date), likewise for Reviewed. Do not invent a day if the source only provides a month/year.
- Multi-selects such as Tags and Guests use the schema's JSON-array representation; a JSON-encoded string of option names was verified with this connector. Read back to ensure individual options were set.
- For database items, use the live title property (normally Name), not the standalone-page `title` property.

## Tags

Reuse existing spellings and granularity before adding synonyms. Choose tags from substantive discussion, not incidental mentions or promotional keywords. Keep people in Host/Guests and the show in Show rather than duplicating them as topic tags.

Examples of useful distinct topics: **Deterrence**, **Nuclear ethics**, **Sovereignty**, **NATO**. Add geography when it is central to the argument, such as **United Kingdom**, **Russia**, or **Ukraine**. A general category such as **Geopolitics** can coexist with these. Avoid value judgments such as “debunked” or ideological labels inferred about a person. Tags are retrieval aids, not fact-check verdicts.

## Duplicate-safe writes

1. Query the fetched data source for the canonical Episode ID. Use supported row/view queries or bounded SQL; SQL identifiers must come from the fetched schema and untrusted values must be bound parameters.
2. If no ID match exists, check the canonical Spotify URL for older records lacking the ID. Do not identify duplicates by analysis title alone. Account for pagination before declaring no match.
3. For one match, fetch it and update the requested content/properties. Preserve user notes, comments, relations, cover, icon, and unrelated blocks. Prefer targeted edits over replacing the whole page.
4. For multiple matches, inspect them before deciding which page to update. Do not silently delete or merge user content.
5. For no match, create one page under the actual data source. Await async completion before dependent actions. On ambiguous failure, re-query before a bounded retry.

## Hub and views

The hub needs a short introduction, the meaning of coverage/review status, and a linked episode view. Keep database pages as the canonical analyses; avoid maintaining a second manual index with duplicate summaries.

Useful initial views:

- **All episodes:** table, Published descending; show Name, Show, Published, Duration (min), Tags, Review status. Quick filters for Show, Tags, Guests, Review status.
- **By topic:** board grouped by Tags; an episode may appear under several topics without being a duplicate page.
- **Needs review:** Review status is Partial or Needs transcript; expose Coverage and Transcript source.
- **Browse episodes:** compact linked table on the hub using the same data source.

Read `notion://docs/view-dsl-spec` through Notion fetch before configuring views. A linked view belongs to a page; additional tabs belong to the database. Native page/database mentions should use the connector's enhanced Markdown, not invented syntax. Do not accidentally move an existing database by using structural tags as if they were links.

After publication, fetch the episode and hub, and query the relevant view. Confirm the original page survived any move, properties have the right types and values, and one underlying episode record appears. Preserve existing views on repeat runs unless the request requires changing them.
