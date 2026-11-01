# Video and reading sources

## YouTube and other videos

Identify the exact video ID, canonical watch URL, title, channel/creator, publication date, runtime, and language from the actual source. Prefer available service tools; otherwise inspect the linked browser. Do not substitute a reaction video or differently edited upload without identifying the change.

The built-in browser may expose `tab.content.exportYouTubeTranscript()` for an HTTPS YouTube `/watch` tab. Use it only when advertised by the current browser API; it returns a local UTF-8 text file. Read that file completely in bounded chunks, inspect whether it includes timestamps and caption provenance, and do not infer missing information. An export failure is not proof that no UI transcript exists.

If needed, use the video's visible **Show transcript** interface. Inspect the language/track and whether captions are automatic or creator-supplied. Read through the end; scrolling, virtualization, or export truncation can leave gaps. Preserve timestamps, speaker uncertainty, ads, and version differences. Use official description chapters when available; label analyst-created chapters separately.

Automatic captions can corrupt names, amounts, currencies, and technical terms while leaving plausible sentences. Preserve the raw export privately. Verify consequential corrections against the audio, visible source material, or primary references; distinguish a transcription correction from a factual correction to the creator's argument. If the export and player controls disagree about caption availability, inspect the actual transcript before declaring it unavailable. Unresolved wording or numbers should remain qualified rather than silently repaired.

Captions do not capture every chart, demonstration, slide, or on-screen statement. Inspect consequential visual material when the tools support it, or explicitly scope the analysis to the transcript. Do not claim to have watched the whole video from captions. Keep captions tied to the upload whose timing they describe.

If captions/transcript are inaccessible, try the relevant official publisher transcript or user-supplied text. Do not substitute the video description for its arguments. Record partial coverage or Needs transcript when appropriate; do not promise unsupported audio transcription.

## Articles, essays, papers, and book excerpts

Read the actual requested text, not just a search snippet, abstract, landing page, or review. For web articles use the canonical publisher page and retain headings and footnotes relevant to the argument. For PDFs, use suitable document tools and check whether the file is digital text or OCR; inspect important figures/tables visually when text extraction omits them. Use an applicable PDF/document skill when that work benefits from it.

For Substack and other newsletters, resolve the individual post and author/publication rather than summarizing the publication homepage. Distinguish the article from recommendations, comments, and subscription prompts. Use an available authenticated session for legitimately accessible subscriber text; an excerpt or paywall preview establishes only partial coverage.

Record title, author(s), publication/publisher, publication date, edition/revision, DOI or canonical URL, language, and requested scope where available. For a chapter/excerpt, distinguish the chapter title and pages from the parent book's title and edition. Do not fabricate a date, author, page count, DOI, or reading duration.

Use headings/section names as locators for unpaginated HTML. Use chapter and printed page numbers for books/PDFs when available, noting PDF page indices if they differ. Do not invent paragraph numbering or transfer page numbers between editions. If only a sample is accessible, say which portions were read and mark Partial text.

Build the source map around the argument's progression rather than forcing timestamps onto text. For empirical research, explain the question, design/data, result, causal limits, and whether broader claims exceed the result. Separate the author's propositions from your critique and distinguish an empirical observation from a normative conclusion.

For a reading without chapters, leave Chapter count empty; its section map can live in the body. Keep Duration (min) empty unless the source actually has audiovisual runtime. Use Text source to identify Article text, PDF text, OCR, Publisher, or User supplied as appropriate. Full text coverage requires reading the full requested scope, including consequential qualifications and notes.

## HTML snapshots and analyst locators

For a public page or legitimately acquired HTML, the dependency-free helper preserves text blocks, source links, image references, hashes, and analyst locators:

```sh
python3 scripts/extract_webpage.py --url 'https://example.org/essay' \
  --container-id essay --output /private/archive/essay
```

Run from the skill directory. Use `--html /private/page.html` with the original `--url` for an acquired snapshot. The container ID must be observed in the actual source. Without it, the helper selects a unique article/main or the body and records that boundary. Compare the extracted title, start, end, headings, and consequential footnotes with the original. Remove navigation and duplicated mobile text without losing qualifications; isolate actual source containers on multi-work pages.

The helper handles HTML text, not JavaScript execution, OCR, authentication, or visual interpretation. Use the linked browser and suitable document tools when needed. Images/tables require separate inspection. Its extraction status starts **not_read**; record actual reading coverage separately as it happens.

`B001` and similar IDs are analyst block locators in the exact hashed snapshot, not publisher paragraph numbers or web anchors. Use short opening phrases to help a reader find cited passages. Re-extraction can change these labels, requiring renewed claim-to-source checks. Keep snapshots in a new or empty private directory outside the public repository.

## Common boundaries

Source accessibility is not permission to republish a full transcript, article, or book. Publish original paraphrases, concise necessary quotations within applicable limits, locators, and links. Keep temporary extracts outside public repositories. Do not bypass a paywall or authentication boundary; work with legitimately available material and disclose any gaps.
