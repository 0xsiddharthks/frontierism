#!/usr/bin/env python3
"""Extract a public or locally acquired HTML text into a private, located snapshot.

No dependencies, credentials, JavaScript execution, or reading-completion claims.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

VOID = set("area base br col embed hr img input link meta param source track wbr".split())
SKIP = set("script style noscript svg nav header footer form dialog".split())
BLOCKS = set("p h1 h2 h3 h4 h5 h6 ul ol blockquote pre table figure hr".split())


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list = field(default_factory=list)

    @property
    def skipped(self):
        return (self.tag in SKIP or "hidden" in self.attrs
                or self.attrs.get("aria-hidden", "").lower() == "true")

    def walk(self):
        yield self
        if not self.skipped:
            for item in self.children:
                if isinstance(item, Node):
                    yield from item.walk()

    def text(self):
        if self.skipped:
            return ""
        if self.tag == "br":
            return "\n"
        text = "".join(x.text() if isinstance(x, Node) else x for x in self.children)
        return text + ("\n" if self.tag in BLOCKS | {"li", "td", "th", "tr", "figcaption"} else "")

    def clean(self):
        return re.sub(r"\s+", " ", self.text()).strip()


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: v or "" for k, v in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        self.stack[-1].children.append(text)


def text_blocks(node):
    """Yield outer semantic blocks once, keeping direct/unwrapped text too."""
    if node.skipped:
        return
    if node.tag in BLOCKS:
        if node.clean():
            yield node
        return
    pending = []
    for child in node.children:
        if isinstance(child, str):
            pending.append(child)
        elif child.tag not in BLOCKS and not any(n.tag in BLOCKS for n in child.walk()):
            pending.append(child)
        else:
            block = Node("text", children=pending)
            if block.clean():
                yield block
            pending = []
            yield from text_blocks(child)
    block = Node("text", children=pending)
    if block.clean():
        yield block


def extract(html: str, url: str, container_id: str | None = None):
    doc = Document(html)
    all_nodes = list(doc.root.walk())
    warnings = []
    if container_id:
        matches = [n for n in all_nodes if n.attrs.get("id") == container_id]
        if len(matches) != 1:
            raise ValueError(f"Expected one container #{container_id}; found {len(matches)}")
        scope, boundary = matches[0], f"id:{container_id}"
    else:
        candidates = [n for n in all_nodes if n.tag == "article"]
        if len(candidates) != 1:
            candidates = [n for n in all_nodes if n.tag == "main"]
        if len(candidates) != 1:
            candidates = [n for n in all_nodes if n.tag == "body"]
        if len(candidates) != 1:
            raise ValueError("No unambiguous article, main, or body; provide --container-id")
        scope, boundary = candidates[0], candidates[0].tag
        warnings.append("Automatic boundary requires comparison with the rendered original.")
    nodes = list(scope.walk())
    blocks = []
    for n in text_blocks(scope):
        links = [{"text": a.clean(), "url": urljoin(url, a.attrs["href"])}
                 for a in n.walk() if a.tag == "a" and a.attrs.get("href")]
        blocks.append({"locator": f"B{len(blocks)+1:03d}", "kind": n.tag,
                       "source_id": n.attrs.get("id"), "text": n.clean(), "links": links})
    if not blocks:
        raise ValueError("Selected container has no text blocks")
    images = [{"url": urljoin(url, n.attrs.get("src") or n.attrs.get("data-src", "")),
               "alt": n.attrs.get("alt", ""), "inspection": "not_inspected"}
              for n in nodes if n.tag == "img"]
    if images or any(n.tag == "table" for n in nodes):
        warnings.append("Images/tables require inspection; plain text does not establish visual evidence.")
    canonical = next((urljoin(url, n.attrs["href"]) for n in all_nodes
                      if n.tag == "link" and "canonical" in n.attrs.get("rel", "").split()
                      and n.attrs.get("href")), url)
    title = next((n.clean() for n in all_nodes if n.tag == "title"), "")
    content = "\n\n".join(b["text"] for b in blocks)
    return {"schema_version": 1, "requested_url": url, "canonical_url": canonical,
            "html_title": title, "boundary": boundary,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "hashes": {"html_sha256": digest(html), "text_sha256": digest(content)},
            "locator_basis": "Analyst block IDs in this exact extracted snapshot; not publisher paragraph numbers.",
            "blocks": blocks, "images": images, "word_count": len(content.split()),
            "warnings": warnings, "coverage": {"status": "not_read", "ranges_read": []}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--html", type=Path)
    parser.add_argument("--container-id")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if urlparse(args.url).scheme not in {"http", "https"}:
        parser.error("--url must be an HTTP(S) source identity")
    destination = args.output.expanduser().resolve()
    repository = Path(__file__).resolve().parents[3]
    if destination.is_relative_to(repository):
        parser.error("Source snapshots must remain outside the public repository")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        parser.error("Use a new or empty output directory to preserve earlier snapshots")
    if args.html:
        raw = args.html.read_bytes()
        html = raw.decode("utf-8-sig")
        final_url = args.url
    else:
        req = Request(args.url, headers={"User-Agent": "Mozilla/5.0 (compatible; CloseReadingArchive/1.0)"})
        with urlopen(req, timeout=45) as response:
            if "html" not in response.headers.get("Content-Type", "").lower():
                parser.error("Source is not HTML; use a suitable document reader")
            raw = response.read()
            html = raw.decode(response.headers.get_content_charset() or "utf-8")
            final_url = response.url
    result = extract(html, final_url, args.container_id)
    result["requested_url"] = args.url
    result["final_url"] = final_url
    result["hashes"]["raw_sha256"] = digest(raw)
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination.chmod(0o700)
    (destination / "original.html").write_bytes(raw)
    (destination / "source.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "source.txt").write_text("\n\n".join(
        f"[{b['locator']} | {b['kind']}] {b['text']}" for b in result["blocks"]) + "\n", encoding="utf-8")
    for name in ("original.html", "source.json", "source.txt"):
        (destination / name).chmod(0o600)
    print(json.dumps({"output": str(destination), "blocks": len(result["blocks"]),
                      "words": result["word_count"], "warnings": result["warnings"]}))


if __name__ == "__main__":
    main()
