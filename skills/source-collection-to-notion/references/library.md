# Ordered study library profile

Use this profile for an explicitly requested new study collection, not an ordinary batch in an existing Research Library. Inspect a supplied example and live Notion capabilities before creating anything. Keep all destination IDs in the private manifest. If no parent was named, the new full-page database can remain private and top-level; do not infer permission to move or share it.

The coordinator owns this profile and all shared changes. Every member still uses the same source-to-notion analytical method. Apply the shared [publishing and readback workflow](../../source-to-notion/references/publishing.md); native appearance inspection stays in the in-app browser first. Existing collections retain their live schema and user customizations.

## Native schema

Use the user's existing naming conventions where possible. For a new reading corpus, a useful schema is:

- Name (title): source number plus a readable analytical title.
- Number (number): source ordinal; guides get separate deliberate sort positions without renumbering sources.
- Kind (select): Text and Guide, or source-specific terms such as Paper.
- Author (select or rich text): supported attribution, with qualification where disputed.
- Topics (multi-select): a few substantive topics from a shared vocabulary.
- Reading (select): To read, Reading, Review, Confident. The learner owns this field.
- Review on (date): initially empty; learner-owned.
- Source (URL), Original title (rich text), Published (date, only if known), Source words (number).
- Prepared (date) and QA (select): production status kept separate from learner progress.

Adapt this profile to the actual source collection: use creators/speakers and relevant runtime or transcript coverage for audio/video, without copying inapplicable fields wholesale. Use an appropriate Source context details group when Text context would be misleading. Add a corpus section/part when it meaningfully improves navigation. Do not mechanically add video/transcript/figure fields to a text-only collection. Explain contested authorship and date discrepancies in context; an uncertain original date can remain empty.

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

The coordinator verifies the exact expected members, unique page mappings, guides, saved views/layout, dynamic review logic, and native navigation. Set production QA through a documented property update after the applicable checks pass and fetch the stored value. Retain before/after evidence in the private ledger. These checks complement per-source content review and do not certify every source claim.
