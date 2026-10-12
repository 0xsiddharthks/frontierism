#!/usr/bin/env python3
"""Validate private lecture drafts against extraction and optional Notion readback.

This checks identities, declared coverage, integrity, and publication evidence.
It cannot establish that a person read a source, viewed an image, wrote a faithful
summary, or classified derived material correctly; those require semantic review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def normalized_url(value):
    if not isinstance(value, str):
        return ""
    parts = urlsplit(value.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query, ""))


def normalized_text(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value or "")).strip()


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


class Audit:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def require(self, condition, message):
        if not condition:
            self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)


def load_object(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def check_id_list(audit, value, expected, label):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        audit.errors.append(f"{label} must be a list of string IDs")
        return
    audit.require(len(value) == len(set(value)), f"{label} contains duplicate IDs")
    missing = set(expected) - set(value)
    extra = set(value) - set(expected)
    if missing:
        audit.errors.append(f"{label} is missing {len(missing)} IDs: {', '.join(sorted(missing)[:12])}")
    if extra:
        audit.errors.append(f"{label} has unknown IDs: {', '.join(sorted(extra)[:12])}")


def check_budget(audit, record, label, primary=False):
    words_key = "source_derived_words" if primary else "derived_words"
    limit_key = "source_word_limit" if primary else "word_limit"
    quote_limit_key = "source_quote_limit" if primary else "quote_limit"
    words, quotes = record.get(words_key), record.get("quoted_words")
    limit, quote_limit = record.get(limit_key, 200), record.get(quote_limit_key, 25)
    for key, value in [(words_key, words), ("quoted_words", quotes), (limit_key, limit), (quote_limit_key, quote_limit)]:
        audit.require(integer(value) and value >= 0, f"{label}.{key} must be a nonnegative integer")
    if not all(integer(v) and v >= 0 for v in [words, quotes, limit, quote_limit]):
        return
    audit.require(quotes <= words, f"{label}: quoted words cannot exceed all derived words")
    audit.require(words <= limit, f"{label}: {words} derived words exceed declared limit {limit}")
    audit.require(quotes <= quote_limit, f"{label}: {quotes} quoted words exceed declared limit {quote_limit}")
    basis = record.get("rights_basis")
    audit.require(isinstance(basis, str) and bool(basis.strip()), f"{label}.rights_basis is required")
    if basis == "protected-web-default":
        audit.require(limit <= 200 and quote_limit <= 25, f"{label}: default protected web limits cannot be raised")
    elif isinstance(basis, str) and basis.strip():
        evidence = record.get("rights_evidence")
        audit.require(isinstance(evidence, str) and bool(evidence.strip()), f"{label}.rights_evidence is required for a nondefault basis")


def validate(source, notes, source_path, allow_draft=False, readback=None, require_published=False):
    audit = Audit()
    audit.require(notes.get("schema_version") == 1, "notes.schema_version must be 1")
    number = source.get("lecture_number")
    audit.require(integer(number), "source.lecture_number must be an integer")
    audit.require(notes.get("lecture_number") == number, "lecture_number does not match source")
    if source.get('course_id') or notes.get('course_id'):
        audit.require(bool(source.get('course_id')) and source.get('course_id') == notes.get('course_id'), 'course_id does not match source')
        audit.require(notes.get('source_label') == source.get('source_label'), 'source_label does not match source')
    title = notes.get("title")
    audit.require(isinstance(title, str) and bool(title.strip()), "notes.title is required")
    source_urls = {normalized_url(source.get("source_url")), normalized_url(source.get("canonical_url"))} - {""}
    audit.require(normalized_url(notes.get("source_url")) in source_urls, "notes.source_url does not match source")
    expected_hash = source.get("hashes", {}).get("article_text_sha256")
    audit.require(isinstance(expected_hash, str) and bool(re.fullmatch(r"[0-9a-f]{64}", expected_hash)), "source article_text_sha256 is invalid")
    audit.require(notes.get("source_sha256") == expected_hash, "notes.source_sha256 does not match extracted article text")

    blocks = source.get("blocks", [])
    audit.require(isinstance(blocks, list) and bool(blocks), "source.blocks must be a nonempty list")
    blocks = blocks if isinstance(blocks, list) else []
    source_ids = [b.get("id") for b in blocks if isinstance(b, dict)]
    audit.require(all(isinstance(i, str) and i for i in source_ids), "source blocks contain invalid IDs")
    audit.require(len(source_ids) == len(set(source_ids)), "source block IDs are not unique")
    coverage = notes.get("coverage", {})
    if not isinstance(coverage, dict):
        audit.errors.append("notes.coverage must be an object")
        coverage = {}
    check_id_list(audit, coverage.get("read_source_ids"), source_ids, "coverage.read_source_ids")

    for anchor in notes.get("anchors", []):
        if not isinstance(anchor, dict) or not isinstance(anchor.get("source_ids"), list):
            audit.errors.append("each optional anchor must contain a source_ids list")
            continue
        audit.require(bool(anchor["source_ids"]), "an anchor cannot point to an empty source ID list")
        audit.require(all(i in source_ids for i in anchor["source_ids"]), f"anchor {anchor.get('label', '')!r} has unknown source IDs")

    source_figures = source.get("figures", [])
    source_figures = source_figures if isinstance(source_figures, list) else []
    figure_ids = [f.get("id") for f in source_figures if isinstance(f, dict)]
    figures = notes.get("figures")
    if not isinstance(figures, list) or any(not isinstance(f, dict) for f in figures):
        audit.errors.append("notes.figures must be a list of objects")
        figures = []
    check_id_list(audit, [f.get("source_id") for f in figures], figure_ids, "figures.source_id")
    for figure in figures:
        label = f"figure {figure.get('source_id', '<missing>')}"
        audit.require(figure.get("status") in {"inspected", "unavailable", "duplicate", "decorative"}, f"{label}: invalid inspection status")
        audit.require(figure.get("disposition") in {"linked", "embedded", "omitted"}, f"{label}: invalid disposition")
        audit.require(isinstance(figure.get("note"), str) and bool(figure["note"].strip()), f"{label}: an inspection/disposition note is required")
        audit.require(not (figure.get("status") == "unavailable" and figure.get("disposition") == "embedded"), f"{label}: cannot claim a verified embed for an uninspected unavailable image")

    checks = notes.get("audit", {})
    if not isinstance(checks, dict):
        audit.errors.append("notes.audit must be an object")
        checks = {}
    for flag in ["full_source_read", "semantic_reviewed"]:
        audit.require(checks.get(flag) is True, f"audit.{flag} must attest to completed review")
    if not allow_draft:
        audit.require(checks.get("draft_ready") is True, "audit.draft_ready must be true")
    limitations = checks.get("limitations")
    audit.require(isinstance(limitations, list) and all(isinstance(v, str) for v in limitations), "audit.limitations must be a list of strings")
    if any(f.get("status") == "unavailable" for f in figures):
        audit.require(bool(limitations), "unavailable source figures require a visible limitation")
    check_budget(audit, checks, "audit", primary=True)
    budgets = checks.get("source_budgets", [])
    if not isinstance(budgets, list) or any(not isinstance(b, dict) for b in budgets):
        audit.errors.append("audit.source_budgets must be a list of objects")
        budgets = []
    for index, budget in enumerate(budgets):
        audit.require(normalized_url(budget.get("url")).startswith(("http://", "https://")), f"source_budgets[{index}].url must be an HTTP(S) URL")
        check_budget(audit, budget, f"source_budgets[{index}]")

    integrity = source.get("integrity", {})
    for flag in ["article_closing_tag_present", "block_text_equals_article_text"]:
        audit.require(integrity.get(flag) is True, f"source integrity failed: {flag}")
    audit.require(integrity.get("paywall_detected") is False, "source integrity is paywalled or not established")
    reviewed_warnings = checks.get("source_warnings_reviewed", [])
    audit.require(isinstance(reviewed_warnings, list), "audit.source_warnings_reviewed must be a list")
    reviewed_warnings = reviewed_warnings if isinstance(reviewed_warnings, list) else []
    for warning in integrity.get("warnings", []):
        audit.require(warning in reviewed_warnings, f"unresolved source warning: {warning}")
    if integrity.get("warnings"):
        audit.require(bool(limitations), "reviewed source warnings need their implications recorded in limitations")

    for filename, hash_key in [("original.html", "original_html_sha256"), ("article.html", "article_html_sha256"), ("article.txt", "article_text_sha256")]:
        path = source_path.parent / filename
        if path.exists():
            data = path.read_bytes()
            if filename == "article.txt" and data.endswith(b"\n"):
                data = data[:-1]
            audit.require(hashlib.sha256(data).hexdigest() == source.get("hashes", {}).get(hash_key), f"archived file hash mismatch: {filename}")
        else:
            audit.warn(f"Archived file unavailable for hash recheck: {filename}")

    properties = notes.get("properties", {})
    if not isinstance(properties, dict):
        audit.errors.append("notes.properties must be an object")
        properties = {}
    for key in ["Name", "Lecture", "Kind", "Topics", "Reading", "Source words", "Figures", "QA"]:
        audit.require(key in properties, f"missing property: {key}")
    audit.require(properties.get("Name") == title, "properties.Name must equal notes.title")
    audit.require(properties.get("Lecture") == number, "properties.Lecture does not match source")
    audit.require(properties.get("Kind") in {"Lecture", "Discussion", "Exam", "Meeting", "Bonus", "Session"}, "properties.Kind must describe a course item")
    audit.require(normalized_url(properties.get("Source", properties.get("Source URL"))) in source_urls, "Source property does not match source")
    audit.require(properties.get("Source words") == source.get("counts", {}).get("words"), "Source words property does not match source counts")
    audit.require(properties.get("Figures") == len(source_figures), "Figures property does not match extracted inventory")
    topics = properties.get("Topics")
    audit.require(isinstance(topics, list) and bool(topics) and all(isinstance(t, str) and t.strip() for t in topics), "Topics must be a nonempty list of strings")
    for key, value in properties.items():
        if key.startswith("date:") and key.endswith(":start"):
            audit.require(isinstance(value, str) and bool(re.match(r"^\d{4}-\d{2}-\d{2}(?:T.*)?$", value)), f"invalid date property: {key}")
    if source.get("published_at") and properties.get("date:Published:start"):
        audit.require(properties["date:Published:start"][:10] == source["published_at"][:10], "Published property does not match source publication date")
    if str(source.get("source_label", "")).upper().strip("# ") == "END":
        audit.require(bool(re.search(r'\bEND\b', str(title), re.I)), "title must preserve the source END label")

    content = notes.get("content")
    audit.require(isinstance(content, str) and bool(content.strip()), "notes.content must contain the complete page body")
    if isinstance(content, str):
        audit.require(any(url in content for url in source_urls), "content must link the source article")
        audit.require(not re.search(r"\b(?:TODO|TBD|FIXME)\b|\[INSERT[^\]]*\]", content), "content contains unfinished placeholders")
        audit.require(not re.search(r"\]\((?:file://|/Users/|/home/|\.\./)", content), "content presents a local filesystem path as a working Notion link")
        for figure in figures:
            original = next((f for f in source_figures if f.get("id") == figure.get("source_id")), {})
            if figure.get("disposition") in {"linked", "embedded"}:
                url = original.get("url")
                audit.require(isinstance(url, str) and url in content, f"figure {figure.get('source_id')}: declared link/embed URL is absent from content")
                if figure.get("disposition") == "embedded" and isinstance(url, str):
                    pattern = r"!\[[^\]]*\]\(" + re.escape(url) + r"\)"
                    audit.require(bool(re.search(pattern, content)), f"figure {figure.get('source_id')}: embedded means a native image block, not only a link")

    if require_published:
        audit.require(readback is not None, "a complete readback record is required")
    if readback is not None:
        validate_readback(audit, notes, readback)
    return {
        "ok": not audit.errors,
        "stage": "publication" if readback is not None or require_published else "draft",
        "lecture_number": number,
        "errors": audit.errors,
        "warnings": audit.warnings,
        "counts": {"source_blocks": len(blocks), "source_figures": len(source_figures), "content_words": len(normalized_text(content if isinstance(content, str) else "").split())},
        "review_boundary": "Coverage and semantic-review fields are attestations; validation does not prove reading, visual inspection, fidelity, or copyright classification.",
    }


def validate_readback(audit, notes, record):
    publication = notes.get("publication", {})
    for key in ["page_id", "parent_id"]:
        audit.require(isinstance(publication.get(key), str) and bool(publication[key]), f"notes.publication.{key} is required")
        audit.require(record.get(key) == publication.get(key), f"readback {key} does not match publication ledger")
    audit.require(record.get("lecture_number") == notes.get("lecture_number"), "readback lecture_number does not match draft")
    audit.require(record.get("complete") is True, "readback must be complete")
    audit.require(record.get("truncated") is False, "readback must explicitly be untruncated")
    audit.require(record.get("errors") == [], "readback contains errors or does not attest to zero errors")
    audit.require(record.get("unknown_block_count") == 0 and integer(record.get("unknown_block_count")), "readback unknown_block_count must be zero")
    audit.require(isinstance(record.get("checked_at"), str) and bool(record["checked_at"].strip()), "readback checked_at is required")
    actual_properties = record.get("properties", {})
    if not isinstance(actual_properties, dict):
        audit.errors.append("readback.properties must be an object")
        actual_properties = {}
    for key, expected in notes.get("properties", {}).items():
        actual = actual_properties.get(key)
        if isinstance(expected, list) and isinstance(actual, list):
            same = sorted(expected) == sorted(actual)
        else:
            same = expected == actual
        audit.require(same, f"readback property differs or is missing: {key}")
    verification = record.get("verification", {})
    if not isinstance(verification, dict):
        verification = {}
    for flag in ["links_valid", "rendering_reviewed"]:
        audit.require(verification.get(flag) is True, f"readback verification.{flag} must be true")
    actual_content = record.get("content")
    audit.require(isinstance(actual_content, str) and bool(actual_content.strip()), "readback must contain the complete fetched body")
    if isinstance(actual_content, str) and normalized_text(actual_content) != normalized_text(notes.get("content")):
        note = verification.get("content_equivalence_note")
        reviewed = verification.get("content_equivalent") is True and isinstance(note, str) and bool(note.strip())
        audit.require(reviewed, "readback body differs; resolve it or record a reviewed serialization-equivalence explanation")
        if reviewed:
            audit.warn("Readback body equality relies on the recorded serialization-equivalence review")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--notes", required=True, type=Path)
    parser.add_argument("--readback", type=Path)
    parser.add_argument("--require-published", action="store_true")
    parser.add_argument("--allow-draft", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = validate(load_object(args.source), load_object(args.notes), args.source, args.allow_draft, load_object(args.readback) if args.readback else None, args.require_published)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {"ok": False, "errors": [f"Unable to validate inputs: {exc}"], "warnings": []}
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    sys.stdout.write(output)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
