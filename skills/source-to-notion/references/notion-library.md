# Research Library conventions

These conventions cover direct source records and ordinary batches in the mixed library. A collection coordinator can supply a different verified destination and schema. Do not load or migrate this default library during draft-only source work.

## Destination and full-page database

Read `${XDG_CONFIG_HOME:-$HOME/.config}/source-to-notion/destination.json`. Version 2 uses `schema_version`, `hub_kind` (`database`), `hub_url`, `database_id`, `data_source_id`, and `default_view_id`. These private destination IDs stay outside the public repository; they are not credentials.

Fetch the configured database and live schema. The database itself is the hub, with a **list** as its main view. Do not create a wrapper page containing a nested database. Use its data source ID as the parent for analysis pages. A database ID is not a regular parent page ID.

If the new configuration is absent, the legacy `spotify-podcast-to-notion/destination.json` in the same config root may identify the existing library. Fetch its database ID and use that database, not the old `hub_page_id` wrapper. Migrate only after verifying the destination. A destination explicitly supplied by the user takes precedence.

If neither configuration exists, search for **Research Library** (and legacy **Podcast Research** when relevant), then inspect plausible matches. Ask only if the intended destination remains ambiguous, while continuing independent analysis. If no library exists and the user requested saving one, create a private full-page Research Library database and its list view. Save verified IDs locally. Do not silently relocate other collections or change their sharing.

## Native properties

Fetch before writing; respect deliberate renames/customizations. Add needed fields without rebuilding the database. New select options for actual formats, sources, people, and subjects are expected.

| Property | Type | Meaning |
| --- | --- | --- |
| Name | Title | Readable analysis title. |
| Source title | Rich text | Exact original title. |
| Content type | Select | Podcast; Video; Reading. A video podcast remains Podcast. |
| Source platform | Select | Spotify; YouTube; Web; File; Print; User supplied. |
| Source URL | URL | Canonical URL without tracking parameters, when available. |
| Source ID | Rich text | Namespaced stable identity; see below. |
| Creators | Rich text | Verified author(s), creator(s), or host(s); not workspace People references. |
| Guests | Multi-select | Interview guests, one name per option. Empty when inapplicable. |
| Series / publication | Select | Show, channel, journal, magazine, or series as relevant. |
| Publisher | Rich text | Organization credited by the source. |
| Publisher page | URL | Alternate official source page, if useful. |
| Published | Date | Publication/release date at known precision; note conflicts or edition dates in the body. |
| Duration (min) | Number | Actual audiovisual runtime in decimal minutes, not an invented reading time. |
| Format | Select | Video podcast, Audio podcast, Video, Article, Essay, Research paper, Book, Book chapter, Report, or another verified format. |
| Language | Select | Source language. |
| Chapter count | Number | Count in the primary chapter scheme when applicable; zero means confirmed none, empty means unknown/inapplicable. |
| Tags | Multi-select | Substantive topics, institutions, and places discussed. |
| Text source | Select | Spotify automatic, YouTube automatic, YouTube creator captions, Publisher, Article text, PDF text, OCR, User supplied, Audio transcription, Unavailable. |
| Coverage | Select | Full transcript, Partial transcript, Full text, Partial text, Metadata only; legacy Episode notes only remains readable. |
| Review status | Select | Analyzed; Partial; Needs transcript; Needs source. |
| Fact-check scope | Select | Targeted checks; Not independently checked. |
| Reviewed | Date | Last substantive analysis review date in the user's timezone. |

Specify editorial/automatic provenance and actual scope in the body. Full text can mean the complete requested chapter, provided the title and coverage statement identify that scope; it must not imply the whole book was read. Metadata-only work is not Analyzed. A tags/layout update does not advance Reviewed. None of these labels certifies every source claim.

Follow connector property encoding: numbers are numeric; date fields use `date:Published:start` and `date:Published:is_datetime` (0 for a date), similarly for Reviewed. Multi-selects use the fetched schema's JSON-array representation; JSON-encoded arrays of option names work with this connector. Read back individual values. For database items, use its actual title property (normally Name), not standalone-page `title`.

Legacy renames preserve data: Episode title → Source title; Show → Series / publication; Host → Creators; Spotify → Source URL; Episode ID → Source ID; Transcript source → Text source. Fetch after renaming, then alter renamed fields in a separate call: combining a rename and an alteration of its new name created duplicate properties in this connector. Do not repeat migration blindly or drop old options still in use. SELECT/MULTI_SELECT schema changes must list every option being retained.

## Identity and repeat runs

Use `spotify:episode:<id>` or `youtube:video:<id>` for their respective platforms. For readings, prefer a DOI plus version/scope where needed, otherwise a canonical URL; for a file without a canonical source use a content hash and record edition/scope in the body. Strip tracking parameters, not meaningful identity/version parameters.

Query Source ID before creating, then canonical Source URL for older records. A legacy Spotify ID may be a bare episode ID under Source ID or Episode ID. Account for pagination before declaring no match. Use fetched schema identifiers and bound parameters for SQL. The primary check must not be restricted by a filtered view that hides existing records.

For one match, fetch and update it, preserving notes, comments, relations, cover, icon, and unrelated blocks. Multiple matches require inspection, not silent deletion. Do not automatically merge two platforms' uploads, separate editions, or different chapters merely because titles resemble each other; verify equivalence and preserve version-specific source locations.

After an ambiguous tool failure, query before retrying creation. Wait for asynchronous completion before dependent writes. Structural changes must preserve the original analysis page IDs and contents.

## Classification and display

Content type answers **what medium is this?** Tags answer **what is it about?** Reuse existing spellings and granularity. Add subjects supported by substantive discussion, not incidental words or inferred labels about a person. Keep people and publication names in their own fields.

Examples: Economics, History, Technology, Political philosophy, Neuroscience, Deterrence, Sovereignty. These are examples, not tags to attach universally. Institutions and geography can be useful when central to the source. Tags are retrieval aids, not verdicts such as “debunked.”

Use **All research** as the first/main **list** view, sorted Published descending, with concise properties such as Name, Content type, and Tags. Quick filters can expose Content type, Tags, Source platform, and Review status. Keep By topic and Needs review as optional secondary views; avoid duplicate manual indexes. Needs review includes Partial, Needs transcript, and Needs source.

Read `notion://docs/view-dsl-spec` before view edits. The current connector can create list views but cannot change an existing view's type. For an existing main view, use the linked Notion UI: view menu → Edit view → Layout → List. Re-fetch and reapply displayed properties if the switch resets them. Do not add a second hidden list and claim the main view changed.

For analysis-page layouts, keep the summary easy to reach: pin Content type, Tags, and Review status; place detailed source/evidence metadata in the sidebar and hide empty fields. Read `notion://docs/database-page-layouts` and the current layout before changing it; preserve user customizations.

When replacing a wrapper with a standalone database, move the real database first, verify its new parent and its records, and only then retire the redundant wrapper within the user's authorized reorganization. A linked view is not the underlying data source. Update the local destination and return the new database URL.
