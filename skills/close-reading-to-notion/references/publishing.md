# Notion collection design and verification

Inspect the supplied example and live connector capabilities before creating anything. A requested new corpus gets its own full-page database, not another set of rows in the example's database. Keep all destination IDs in a private manifest. If no parent was named, a new database can remain a private top-level database; do not infer permission to move or share it.

## Browser-first inspection

Always try the built-in in-app browser first when available for Notion inspection and UI changes. Prefer the user's existing tab, or a separate background tab if they are actively using it. Inspect the example, then the new collection's actual saved views and representative study pages. Use the browser for native settings that the connector does not expose, including row icons, full-page opening, and font. Supported connector and CLI operations can still handle structured changes, batch publication, and full-page readback efficiently. See [notion-cli.md](notion-cli.md) for the tested CLI path and its limits.

After each UI change, inspect the new state and verify the saved result. Check the summary and source link, pinned properties and details groups, long titles, folded answers, and native navigation. Do not claim visual verification from a successful connector mutation. If the in-app browser cannot load the page, lacks its authenticated session, or cannot perform the required interaction, explain the observed limitation and use the best available fallback allowed by the user's preferences. Retry when the user reports the browser has been repaired; do not encode a temporary failure as a standing reason to avoid it.

Wait for the destination page's title and identity before opening appearance controls; the old page's Actions button may remain visible during navigation. Use native links or their observed full URLs when a bare-ID navigation is aborted. Reinspect after a failed action instead of repeating it blindly.

## Native schema

Use the user's existing naming conventions where possible. A useful corpus schema is:

- Name (title): source number plus a readable analytical title.
- Number (number): source ordinal; guides get separate deliberate sort positions without renumbering sources.
- Kind (select): Text and Guide, or source-specific terms such as Paper.
- Author (select or rich text): supported attribution, with qualification where disputed.
- Topics (multi-select): a few substantive topics from a shared vocabulary.
- Reading (select): To read, Reading, Review, Confident. The learner owns this field.
- Review on (date): initially empty; learner-owned.
- Source (URL), Original title (rich text), Published (date, only if known), Source words (number).
- Prepared (date) and QA (select): production status kept separate from learner progress.

Add a corpus section/part when it meaningfully improves navigation. Do not mechanically add video/transcript/figure fields to a text-only collection. Explain contested authorship and date discrepancies in context; an uncertain original date can remain empty.

Pin Reading, Topics, and Review on under the title. Put Number, Kind, Author, and Part in a Text context details group, source metadata in Original source, and Prepared/QA in Library record. Hide empty details and decorative property icons where supported. Preserve mandatory title, editor, and discussion modules. Begin page content with the executive summary.

## Views and guides

Use native **List** views. Show only the few useful row properties listed below. Omit page icons on the database, texts, and guides; hide generic icons in rows as a separate setting. Open texts as full pages. Match the example's native font when supported, and verify it visually; do not turn prose into code to imitate a font.

- Reading order: Name, Reading; all texts and guides; Number ascending.
- By topic: Name, Reading; texts only; Topics grouped, Number ascending.
- Reading progress: Name, Review on; texts only; Reading grouped, Number ascending.
- Review queue: Name, Review on, Reading; texts AND (Reading is Review OR Review on is on/before dynamic today); Review on then Number ascending.
- Guides: Name; guides only; Number ascending.
- Details: Name, Author, QA; texts only; Number ascending.

Expose useful unset quick filters for Topics and Reading. Use the connector's documented view DSL and page-layout format; do not guess parameters. If a native setting is unavailable, use the built-in browser and record any unresolved limitation accurately.

Add a start/reading guide explaining the corpus, major questions, concept vocabulary, source edition, and suggested routes. Add one maintenance guide with manifest scope, source provenance, locator convention, private archive location, schema, update instructions, and honest limits. These are Guide rows, distinct from the exact requested text count. Do not put internal incident details or credentials in either guide.

## Draft, publication, and refresh

Keep a private manifest with collection ID, source URL/edition, stable ordinal, snapshot hashes, blocks actually read, draft, Notion page ID, and readback status. Extraction and full reading are distinct states. Persist page IDs after creation; reconcile ambiguous results against the destination before retrying. Do not change sharing permissions.

Before updating, fetch the current page and compare with the saved readback. Make a targeted edit or reconcile concurrent changes. Retain the learner's annotations, progress, review dates, comments, source identity, and existing page ID. A source re-extraction invalidates old block locators until their claims are checked against the new snapshot.

Fetch every created/changed page completely. Check identity and parent, expected metadata, body text, important links, folded answers, and supported blocks. Compare substantive content after only documented lossless serialization changes; a successful response or matching length alone is insufficient. Query the database for every expected ordinal, duplicate source URLs, and reused page IDs. Verify neighboring navigation after the full page mapping exists.

Set QA through the connector's documented property-update operation after the checks pass. Do not assume a content-edit command also applies an accompanying property change; verify the stored value.

Fetch the saved schema, page layout, and each view independently of page bodies. Check List type, grouping, filters, sorts, visible properties, and dynamic review logic. Open representative pages, long titles, grouped lists, and guides in the app. Scope claims accurately: all-page content verification does not mean every page was visually inspected, and structural validation does not prove the arguments are sound.
