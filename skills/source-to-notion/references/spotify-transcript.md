# Spotify transcript access and coverage

## Source order

1. Discover Spotify connector tools. Use episode metadata and chapters when available; do not infer transcript access from metadata access.
2. If needed, open the canonical episode in the user's linked built-in browser, inspect its current UI, and select **Transcript** if present. Use the browser tool's documented APIs and observed locators.
3. If unavailable, inspect the publisher's episode page for a transcript or a matching official release elsewhere. Confirm participants, title/date, runtime, and version before treating another transcript as equivalent.
4. Use user-supplied transcript/audio when offered. Audio transcription requires a supported tool and authorized access to the media; do not promise it when unavailable.

Stop after these relevant routes are exhausted and report the actual access limit. Do not bypass authentication, payment, DRM, or access controls. No connector or source guarantees that every Spotify episode has an extractable transcript.

## Rendering trap observed in Spotify

In one completed extraction, `innerText()` on the Transcript panel returned only the first few minutes, while the loaded panel DOM contained the full text. The complete result contained 549 timestamped blocks from 00:04 through the closing thanks at 1:05:27 for a 1:05:34 episode. These are an example, not an expected count or timestamp for future episodes.

After inspecting the actual Transcript tab and its DOM, a read of child text content recovered the text that was already loaded for that UI:

```javascript
await tab.playwright
  .getByRole("tabpanel", { name: "Transcript", exact: true })
  .evaluate(el => Array.from(el.children).map(child => child.textContent));
```

Use this only if the current tool API and inspected DOM support it. This reads the observed transcript panel, not hidden application state, private APIs, cookies, or network credentials. Do not reuse element IDs or assume the same child structure across versions.

If the UI is actually virtualized or lazy-loaded, DOM text content will also be incomplete. Scroll the transcript panel through its content, collect overlapping visible segments, and reconcile timestamps/text to remove overlap. Repeated dialogue can be real; do not deduplicate by sentence text alone.

Keep extraction results in tool memory or private temporary storage outside public repositories. Avoid dumping a long transcript into a single tool result: truncation can silently remove the middle or end. Read sequential bounded chunks and keep notes tied to their ranges. If any result reports truncation, retrieve smaller chunks before analysis.

## Coverage checks

- Preserve timestamp blocks and their order. Where present, speaker labels must be associated with the right following text, not attached to an entire chapter by assumption.
- Check the opening, transitions, apparent gaps, final spoken segment, and closing against episode runtime. A few seconds of silence/music can explain boundary differences; explicitly investigate larger omissions.
- Verify both acquisition and reading: count/time coverage can diagnose gaps but cannot substitute for reading the content.
- Automatic speaker labels can switch at advertisements or misattribute interruptions. Names and technical terms may be wrong. Qualify uncertain attribution and verify consequential quotations where feasible.
- Record source/runtime disagreements. Dynamic ads or edited releases may shift timestamps; do not silently align versions, and do not assume ads explain a discrepancy without evidence.
- Separate ads and housekeeping from substantive notes. Include gaps and unexamined audio/visual material in limitations.

## Chapters and text notes

Prefer actual source chapter starts. Infer each end from the next start and the final end from the matching runtime; label calculated ends as such. Check monotonic starts and nonnegative durations. Do not invent missing chapters.

Chapter labels can contain appended biography or promotional text. Use a short original topic label and disclose cleanup instead of reproducing irrelevant material. If Spotify and the publisher provide different schemes, name the source of each and avoid merging them into a fictitious official sequence.

Publish original timestamped paraphrases and a link to the source. Keep necessary short quotations within applicable limits. An accessible third-party transcript is evidence for analysis, not automatic permission to republish its full text.
