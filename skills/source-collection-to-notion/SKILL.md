---
name: source-collection-to-notion
description: Coordinate analysis and Notion publication of a bounded source collection or batch using source-to-notion for every source. Use for inventory, dependencies, parallel drafts, collection-wide review, guides, navigation, and verified publication; use source-to-notion for one source and notion-analyze-and-link for a later review of existing notes.
---

# Source collection to Notion

Coordinate a defined set of sources around the user's learning goal. Use [source-to-notion](../source-to-notion/SKILL.md) as the one per-source analytical method. This skill owns collection membership, scheduling, shared state, cross-source review, and publication; it does not maintain a second analysis template.

## Establish the collection and phase constraints

Resolve the requested members, editions/scopes, intended outcome, destination, ordering, and existing collection state. Build an explicit private manifest; inspect pagination, duplicates, redirects, and gaps. Stable source keys and ordinals are different from titles or the order workers finish. Record existing page IDs before any creation.

Several URLs do not automatically authorize a new database or a broad synthesis. Reuse a supplied destination or the existing Research Library for an ordinary batch. An explicitly requested new study collection gets its own database; read [references/library.md](references/library.md) for the ordered library profile. Inspect any supplied example without treating it as the destination. Preserve deliberate schemas and learner content in existing collections.

Record global constraints before dispatch. If the user asks to read and analyze the whole corpus before creating or publishing, enforce a real barrier: all source reading and analysis stay in private drafts until the required scope is ready; do not create the database or guides early. If a source is inaccessible, retain the gap and report it rather than silently shrinking the requested corpus or crossing the barrier. Otherwise choose a sensible staging order without implying the user requested an all-before-publication rule.

Keep manifest, snapshots, worker assignments, drafts, review evidence, source/page mappings, and readbacks outside the public repository. The coordinator owns these shared records.

## Schedule the analysis

Identify which sources can be understood independently and which depend on earlier definitions, context, or evidence. Provide a verified glossary or relevant surrounding context when needed; use dependency-ordered stages for tightly connected material. Do not provide the desired conclusion or homogenize legitimate disagreements.

When agents are available and parallel work adds value, delegate disjoint source units using the shared source-to-notion skill in **draft-only mode**. Respect available capacity and use a bounded worker pool; batch short independent texts when that reduces overhead. Each source has one draft owner. Give workers only the relevant brief, exact identities/scopes, snapshot/version or acquisition instructions, context, and private output paths. Read [references/draft-contract.md](references/draft-contract.md) for the handoff.

Central acquisition can avoid contention for an authenticated browser or ensure that all workers read the same edition. Workers must still read their assigned substantive material and record actual coverage; a coordinator's download does not satisfy their reading. They can investigate legitimate alternatives within the assigned source's scope when access is incomplete.

For a few short sources, strongly sequential material, constrained access, or unavailable delegation, perform the same per-source process sequentially. Parallelism is an execution choice, not a second analytical mode. Workers must not independently choose destinations, change shared schema, edit the same page, publish early, or send external messages.

## Review and reconcile

Collect each readable draft and its evidence record. Check assigned identity/scope, snapshot hash, actual reading coverage, consequential notes/visuals, source locators, and unresolved gaps. Reconcile duplicate or failed jobs by stable source key rather than spawning a second writer blindly. Structural checks establish consistency of records, not proof of reading or interpretation.

Review analytical specificity against the shared source method: the central question, necessary concepts, difficult reasoning step, evidence, decisive assumption, and strongest objection or limitation. Check consequential attributed claims against the relevant original passages. Normalize metadata and topic vocabulary while preserving distinct arguments, explanatory structures, and evidence-backed interpretive disagreement. Resolve contradictions in evidence; do not manufacture consensus.

Cross-source synthesis waits for the constituent analyses. Read the complete relevant analyses and necessary original passages before asserting a relationship. Candidate links from workers are provisional. Distinguish continuation, support, tension, shared assumptions, and different mechanisms; repetition across sources is not independent corroboration. Add substantive connections or synthesis within the requested scope. For a later pass over already published notes, use notion-analyze-and-link separately.

## Publish through one coordinator

The coordinator handles shared database/schema/layout, guides, source/page mapping, and publication order. Follow the shared [publishing workflow](../source-to-notion/references/publishing.md) and the destination's live schema. The coordinator publishes the reviewed drafts; parallel analysis workers remain draft-only. Honor any read/analyze-all barrier before the first creation or publication action.

Persist each successful page ID and reconcile ambiguous results before retrying. Preserve learner notes, comments, progress, review dates, and existing connections. For an ordered study collection, add native previous/next and guide navigation after the complete identity map exists. A new ordered study library gets a reading guide and maintenance/provenance guide. An ordinary batch in a shared library gets no new sequence, guides, or cross-source synthesis unless requested.

Fetch every created/changed page completely and compare its content and metadata with the intended result. Audit exact expected membership, missing/duplicate source identities, edition/scope, and unique page mappings; also verify guide count and navigation for an ordered study collection. Independently inspect saved views/layout and representative rendering in the in-app browser first when available. The shared CLI helper can support bounded complete exports; it does not certify analytical quality.

Report the exact completed scope, Notion destination, real gaps, and what was verified. Distinguish analysis read by delegated agents from original material personally reread by the coordinator. Preserve unresolved work privately and report it as partial or unpublished instead of claiming the whole collection complete.
