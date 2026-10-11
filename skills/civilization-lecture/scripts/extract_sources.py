#!/usr/bin/env python3
"""Archive public Ghost lecture articles without credentials or third-party packages.

Usage:
  python3 extract_sources.py --output /private/path/civilization-study
  python3 extract_sources.py --output /private/path/civilization-study --refresh
  python3 extract_sources.py --output /private/path/civilization-study --lecture 1

The output includes a manifest and directories 01..60. Raw course material must
stay outside a public repository. Requests follow the archive's actual rel=next
links; no private API, login, or access-control bypass is used. The final source
label is END, not 60: an ordinal of 60 is assigned only after inventory verification.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


SCHEMA_VERSION = "1.0"
DEFAULT_INDEX = "https://predictivehistory.com/tag/civilization/"
USER_AGENT = "Mozilla/5.0 (compatible; CivilizationStudyArchive/1.0)"
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
SKIP_TEXT = {"script", "style", "noscript", "svg"}
BLOCK_TYPES = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote", "pre", "figure", "table", "hr", "iframe", "video", "audio"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)
    parent: Node | None = field(default=None, repr=False)
    start: int = 0
    content_start: int = 0
    content_end: int = 0
    end: int = 0

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def text(self) -> str:
        if self.tag in SKIP_TEXT:
            return ""
        if self.tag == "br":
            return "\n"
        value = "".join(child if isinstance(child, str) else child.text() for child in self.children)
        if self.tag in BLOCK_TYPES | {"li", "tr", "td", "th", "figcaption"}:
            return value + "\n"
        return value

    def clean_text(self) -> str:
        return re.sub(r"\s+", " ", self.text()).strip()


class Document(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.lines = [0]
        self.lines.extend(m.end() for m in re.finditer("\n", source))
        self.root = Node("document", end=len(source), content_end=len(source))
        self.stack = [self.root]
        self.feed(source)
        self.close()
        for node in self.stack[1:]:
            node.content_end = node.end = len(source)

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.source_offset()
        end = start + len(self.get_starttag_text())
        node = Node(tag, dict((k, v or "") for k, v in attrs), parent=self.stack[-1], start=start, content_start=end)
        self.stack[-1].children.append(node)
        if tag in VOID:
            node.content_end = node.end = end
        else:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            node = self.stack.pop()
            node.content_end = node.end = node.content_start

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                start = self.source_offset()
                end = self.source.find(">", start) + 1
                for node in self.stack[index:]:
                    node.content_end = start
                    node.end = end
                del self.stack[index:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)

    def outer(self, node: Node) -> str:
        return self.source[node.start:node.end]

    def inner(self, node: Node) -> str:
        return self.source[node.content_start:node.content_end]

    def find(self, tag: str | None = None, class_name: str | None = None) -> Node | None:
        return next((n for n in self.root.walk() if (tag is None or n.tag == tag) and (class_name is None or n.has_class(class_name))), None)


def request(url: str) -> tuple[bytes, dict]:
    """Use a normal public GET and record retrieval evidence; never save cookies."""
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,image/*;q=0.8,*/*;q=0.5"})
            with urlopen(req, timeout=45) as response:
                data = response.read()
                metadata = {
                    "requested_url": url,
                    "final_url": response.url,
                    "retrieved_at": now(),
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "content_length_bytes": len(data),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "sha256": digest(data),
                }
                return data, metadata
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(2 ** attempt)
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Request retries exhausted")


def inventory(index_url: str, output: Path, refresh: bool = False) -> dict:
    saved = output / "inventory.json"
    if saved.exists() and not refresh:
        return json.loads(saved.read_text())
    index_dir = output / "inventory"
    index_dir.mkdir(parents=True, exist_ok=True)
    pages, lectures, visited = [], {}, set()
    url = index_url
    advertised = None
    while url:
        if url in visited:
            raise ValueError(f"Pagination cycle: {url}")
        if urlparse(url).netloc != urlparse(index_url).netloc:
            raise ValueError(f"Unexpected pagination origin: {url}")
        visited.add(url)
        raw, retrieval = request(url)
        source = raw.decode("utf-8")
        doc = Document(source)
        (index_dir / f"page-{len(pages) + 1}.html").write_bytes(raw)
        found = re.search(r"A collection of\s+(\d+)\s+issues", doc.root.clean_text())
        if found and advertised is None:
            advertised = int(found.group(1))
        page_items = []
        for node in doc.root.walk():
            if node.tag == "a" and node.has_class("gh-card-link"):
                heading = next((n for n in node.walk() if n.has_class("gh-card-title")), None)
                title = heading.clean_text() if heading else node.clean_text()
                match = re.match(r"Civilization\s+#(\d+|END)\s*:", title, re.I)
                if not match:
                    raise ValueError(f"Unrecognized lecture card: {title}")
                label = match.group(1).upper()
                absolute = urljoin(url, node.attrs["href"])
                if label in lectures and lectures[label]["url"] != absolute:
                    raise ValueError(f"Duplicate lecture label: {label}")
                lectures[label] = {"source_label": f"#{label}", "title": title, "url": absolute}
                page_items.append(label)
        pages.append({**retrieval, "labels": page_items, "file": f"inventory/page-{len(pages)+1}.html"})
        next_node = next((n for n in doc.root.walk() if n.tag == "link" and "next" in n.attrs.get("rel", "").split()), None)
        url = urljoin(url, next_node.attrs["href"]) if next_node else None
    expected = {str(number) for number in range(1, 60)} | {"END"}
    actual = set(lectures)
    if actual != expected or advertised != 60:
        raise ValueError(f"Course inventory mismatch: advertised={advertised}; missing={sorted(expected-actual)}; extra={sorted(actual-expected)}")
    ordered = []
    for label in [str(number) for number in range(1, 60)] + ["END"]:
        number = 60 if label == "END" else int(label)
        ordered.append({"lecture_number": number, **lectures[label], "directory": f"{number:02}"})
    result = {
        "schema_version": SCHEMA_VERSION,
        "index_url": index_url,
        "retrieved_at": now(),
        "advertised_lecture_count": advertised,
        "lecture_count": len(ordered),
        "pagination_pages": pages,
        "normalization": {"60": "Source title is #END. Ordinal 60 is a library sorting label, justified by the archive declaring 60 issues and exposing exactly #1 through #59 plus #END. It is not a numeric label printed by the source."},
        "lectures": ordered,
        "integrity": {"unique_urls": len({x["url"] for x in ordered}), "missing_numbers": [], "pagination_terminated": True},
    }
    write_json(saved, result)
    return result


def inline_md(node: Node | str, base_url: str) -> str:
    if isinstance(node, str):
        return re.sub(r"\s+", " ", node)
    if node.tag in SKIP_TEXT:
        if node.tag == "script" and "math" in node.attrs.get("type", ""):
            return "$$" + "".join(c for c in node.children if isinstance(c, str)) + "$$"
        return ""
    value = "".join(inline_md(child, base_url) for child in node.children)
    if node.tag in {"strong", "b"}:
        return "**" + value.strip() + "**"
    if node.tag in {"em", "i"}:
        return "*" + value.strip() + "*"
    if node.tag == "code":
        return "`" + value + "`"
    if node.tag == "a" and node.attrs.get("href"):
        return f"[{value.strip()}]({urljoin(base_url,node.attrs['href'])})"
    if node.tag == "img":
        return f"![{node.attrs.get('alt','')}]({urljoin(base_url,node.attrs.get('src',''))})"
    if node.tag == "br":
        return "\n"
    if node.tag in {"sup", "sub"}:
        return f"<{node.tag}>{value}</{node.tag}>"
    return value


def table_rows(node: Node) -> list[list[str]]:
    return [[cell.clean_text() for cell in row.children if isinstance(cell, Node) and cell.tag in {"th", "td"}]
            for row in node.walk() if row.tag == "tr"]


def block_md(node: Node, base_url: str) -> str:
    if re.fullmatch(r"h[1-6]", node.tag):
        return "#" * int(node.tag[1]) + " " + inline_md(node, base_url).strip()
    if node.tag in {"ul", "ol"}:
        items = []
        for index, item in enumerate(n for n in node.children if isinstance(n, Node) and n.tag == "li"):
            prefix = f"{index+1}. " if node.tag == "ol" else "- "
            body = "".join(block_md(c,base_url) if isinstance(c, Node) and c.tag in {"ul", "ol"} else inline_md(c,base_url) for c in item.children)
            items.append(prefix + body.strip().replace("\n", "\n  "))
        return "\n".join(items)
    if node.tag == "blockquote":
        return "\n".join("> " + line for line in inline_md(node, base_url).strip().splitlines())
    if node.tag == "pre":
        return "```\n" + node.text().strip() + "\n```"
    if node.tag == "table":
        rows = table_rows(node)
        if not rows:
            return ""
        width = max(map(len, rows))
        formatted = [[value.replace("|", "\\|").replace("\n", "<br>") for value in row] + [""] * (width-len(row)) for row in rows]
        out = ["| " + " | ".join(formatted[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
        out += ["| " + " | ".join(row) + " |" for row in formatted[1:]]
        return "\n".join(out)
    if node.tag == "hr":
        return "---"
    if node.tag in {"iframe", "video", "audio"}:
        return f"[{node.tag} source]({urljoin(base_url,node.attrs.get('src',''))})"
    if node.tag == "figure":
        return "\n\n".join(inline_md(c,base_url).strip() for c in node.children if inline_md(c,base_url).strip())
    return inline_md(node, base_url).strip()


def content_nodes(node: Node):
    for child in node.children:
        if not isinstance(child, Node):
            if child.strip():
                yield Node("p", children=[child])
            continue
        if child.tag in SKIP_TEXT and not (child.tag == "script" and "math" in child.attrs.get("type", "")):
            continue
        if child.tag in BLOCK_TYPES or child.tag in {"math", "img"}:
            yield child
        elif any(isinstance(c, Node) and (c.tag in BLOCK_TYPES or c.tag == "div") for c in child.children):
            yield from content_nodes(child)
        else:
            yield child


def extract(source: str, url: str, lecture: dict, retrieval: dict) -> dict:
    doc = Document(source)
    article = doc.find(class_name="gh-content")
    if article is None:
        raise ValueError(f"Missing article content: {url}")
    title_node = doc.find("h1")
    title = title_node.clean_text() if title_node else ""
    if title != lecture["title"]:
        raise ValueError(f"Card/article title mismatch: {lecture['title']!r} != {title!r}")
    metadata = {n.attrs.get("property",n.attrs.get("name")): n.attrs.get("content") for n in doc.root.walk() if n.tag == "meta"}
    canonical = next((n.attrs.get("href") for n in doc.root.walk() if n.tag == "link" and n.attrs.get("rel") == "canonical"), url)
    counters, blocks, headings, figures, tables, math = Counter(), [], [], [], [], []
    active_heading = None
    nodes = list(content_nodes(article))
    for index, node in enumerate(nodes):
        tag = node.tag
        kind = "heading" if re.fullmatch(r"h[1-6]",tag) else {"p":"paragraph","ul":"list","ol":"list","figure":"figure","table":"table","img":"figure","blockquote":"quote"}.get(tag, tag)
        counters[kind] += 1
        block_id = f"{kind}-{counters[kind]:03}"
        if kind == "heading":
            active_heading = block_id
            headings.append({"id":block_id,"source_id":node.attrs.get("id"),"level":int(tag[1]),"text":node.clean_text(),"block_index":index})
        block = {"id":block_id,"type":kind,"tag":tag,"source_id":node.attrs.get("id"),"heading_id":active_heading,"text":node.clean_text(),"markdown":block_md(node,url),"html":doc.outer(node)}
        blocks.append(block)
        for image in (n for n in node.walk() if n.tag == "img"):
            container = image.parent
            while container and container != article and container.tag != "figure":
                container = container.parent
            caption = next((n.clean_text() for n in container.walk() if n.tag == "figcaption"), "") if container else ""
            figures.append({"id":f"figure-{len(figures)+1:03}","block_id":block_id,"heading_id":active_heading,"role":"article-figure","url":urljoin(url,image.attrs.get("src",image.attrs.get("data-src",""))),"srcset":image.attrs.get("srcset"),"alt":image.attrs.get("alt",""),"caption":caption,"width":image.attrs.get("width"),"height":image.attrs.get("height"),"source_id":image.attrs.get("id"),"preceding_text":nodes[index-1].clean_text() if index else "","following_text":nodes[index+1].clean_text() if index+1 < len(nodes) else "","alt_missing":not bool(image.attrs.get("alt",""))})
        for table in (n for n in node.walk() if n.tag == "table"):
            tables.append({"id":f"table-{len(tables)+1:03}","block_id":block_id,"rows":table_rows(table),"html":doc.outer(table),"has_spans":any(n.attrs.get("rowspan") or n.attrs.get("colspan") for n in table.walk())})
        for formula in (n for n in node.walk() if n.tag in {"math","sup","sub"} or n.has_class("katex") or (n.tag == "script" and "math" in n.attrs.get("type",""))):
            math.append({"block_id":block_id,"tag":formula.tag,"html":doc.outer(formula),"text":formula.clean_text()})
    links = [{"text":n.clean_text(),"url":urljoin(url,n.attrs["href"])} for n in article.walk() if n.tag == "a" and n.attrs.get("href")]
    embeds = [{"tag":n.tag,"url":urljoin(url,n.attrs.get("src","")),"html":doc.outer(n)} for n in article.walk() if n.tag in {"iframe","video","audio"}]
    outside_images = [{"url":urljoin(url,n.attrs.get("src","")),"alt":n.attrs.get("alt",""),"role":"outside-article/decorative-or-navigation"} for n in doc.root.walk() if n.tag == "img" and not article.start <= n.start < article.end]
    text = "\n\n".join(b["text"] for b in blocks if b["text"])
    article_text = article.clean_text()
    extracted_text = re.sub(r"\s+"," ",text).strip()
    word_count = len(re.findall(r"\S+",text))
    warnings = []
    if article_text != extracted_text:
        warnings.append("block_text_does_not_exactly_match_article_text")
    if word_count < 500:
        warnings.append("short_article_under_500_words")
    paywall_nodes = [n for n in article.walk() if any(v in n.attrs.get("class","") for v in ("gh-post-upgrade-cta","gh-post-cta","paywall"))]
    if paywall_nodes:
        warnings.append("paywall_marker_in_article")
    if len(figures) != sum(n.tag == "img" for n in article.walk()):
        warnings.append("figure_count_mismatch")
    if len(tables) != sum(n.tag == "table" for n in article.walk()):
        warnings.append("table_count_mismatch")
    if not article.end or article.end == len(source):
        warnings.append("article_closing_tag_not_verified")
    return {
        "schema_version":SCHEMA_VERSION,"lecture_number":lecture["lecture_number"],"source_label":lecture["source_label"],"title":title,"source_url":url,"canonical_url":canonical,
        "published_at":metadata.get("article:published_time"),"modified_at":metadata.get("article:modified_time"),"author":metadata.get("author"),"description":metadata.get("description"),"retrieval":retrieval,
        "hashes":{"original_html_sha256":digest(source),"article_html_sha256":digest(doc.inner(article)),"article_text_sha256":digest(text)},
        "counts":{"words":word_count,"characters":len(text),"blocks":len(blocks),"paragraphs":counters["paragraph"],"headings":len(headings),"figures":len(figures),"tables":len(tables),"math_nodes":len(math)},
        "headings":headings,"blocks":blocks,"figures":figures,"tables":tables,"math":math,"links":links,"embeds":embeds,"outside_article_images":outside_images,
        "integrity":{"article_selector":".gh-content","article_closing_tag_present":bool(article.end and article.end < len(source)),"block_text_equals_article_text":article_text == extracted_text,"paywall_detected":bool(paywall_nodes),"first_text":next((b["text"] for b in blocks if b["text"]),""),"last_text":next((b["text"] for b in reversed(blocks) if b["text"]),""),"warnings":warnings},
        "article_html":doc.inner(article),"article_text":text,
    }


def archive_lecture(lecture: dict, output: Path, refresh: bool = False, download_images: bool = False) -> dict:
    directory = output / lecture["directory"]
    directory.mkdir(parents=True, exist_ok=True)
    html_path = directory / "original.html"
    retrieval_path = directory / "retrieval.json"
    if html_path.exists() and retrieval_path.exists() and not refresh:
        raw = html_path.read_bytes()
        retrieval = json.loads(retrieval_path.read_text())
    else:
        raw, retrieval = request(lecture["url"])
        html_path.write_bytes(raw)
        write_json(retrieval_path, retrieval)
    result = extract(raw.decode("utf-8"), lecture["url"], lecture, retrieval)
    (directory / "article.html").write_text(result.pop("article_html"), encoding="utf-8")
    (directory / "article.txt").write_text(result.pop("article_text") + "\n", encoding="utf-8")
    markdown = [f"# {result['title']}", f"Source: {result['canonical_url']}\n\nPublished: {result['published_at']}\n\nSource label: {result['source_label']} | Library ordinal: {result['lecture_number']}\n\nThis is a private extraction of the source article, not an independently verified historical account."]
    for block in result["blocks"]:
        markdown += [f"<a id=\"{block['id']}\"></a>\n\n{block['markdown']}"]
    (directory / "article.md").write_text("\n\n".join(markdown) + "\n",encoding="utf-8")
    if download_images:
        image_dir = directory / "figures"
        image_dir.mkdir(exist_ok=True)
        for figure in result["figures"]:
            suffix = Path(urlparse(figure["url"]).path).suffix or ".bin"
            destination = image_dir / (figure["id"] + suffix)
            image_metadata = destination.with_suffix(destination.suffix + ".json")
            try:
                if destination.exists() and image_metadata.exists() and not refresh:
                    info = json.loads(image_metadata.read_text())
                else:
                    body, info = request(figure["url"])
                    if not info["content_type"] or not info["content_type"].startswith("image/"):
                        raise ValueError(f"Unexpected figure media type: {info['content_type']}")
                    destination.write_bytes(body)
                    write_json(image_metadata, info)
                figure["archive"] = {"file":str(destination.relative_to(output)),**info}
            except Exception as exc:
                figure["archive"] = {"error":str(exc)}
                result["integrity"]["warnings"].append(f"figure_download_failed:{figure['id']}")
    write_json(directory / "source.json",result)
    return {**lecture,"canonical_url":result["canonical_url"],"published_at":result["published_at"],"modified_at":result["modified_at"],"counts":result["counts"],"hashes":result["hashes"],"warnings":result["integrity"]["warnings"],"files":{"source":f"{lecture['directory']}/source.json","markdown":f"{lecture['directory']}/article.md","text":f"{lecture['directory']}/article.txt","original_html":f"{lecture['directory']}/original.html","article_html":f"{lecture['directory']}/article.html"}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--index-url",default=DEFAULT_INDEX)
    parser.add_argument("--lecture",type=int,action="append",help="Select ordinals (repeatable); 60 is source #END")
    parser.add_argument("--refresh",action="store_true")
    parser.add_argument("--download-images",action="store_true")
    parser.add_argument("--workers",type=int,default=4)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    repo = Path(__file__).resolve().parents[3]
    if output == repo or repo in output.parents:
        parser.error("Raw article output must be outside this public skill repository")
    if args.lecture and any(number < 1 or number > 60 for number in args.lecture):
        parser.error("Lecture ordinals must be in 1..60")
    output.mkdir(parents=True,exist_ok=True)
    index = inventory(args.index_url,output,args.refresh)
    selected = [item for item in index["lectures"] if not args.lecture or item["lecture_number"] in args.lecture]
    manifest_path = output / "manifest.json"
    existing = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    archived = {item["lecture_number"]:item for item in existing.get("lectures",[])}
    failures = []
    with ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as executor:
        pending = {executor.submit(archive_lecture,item,output,args.refresh,args.download_images):item for item in selected}
        for future in as_completed(pending):
            item = pending[future]
            try:
                result = future.result()
                archived[item["lecture_number"]] = result
                print(f"{item['lecture_number']:02} {result['counts']['words']} words; {result['counts']['figures']} figures; {result['counts']['tables']} tables; warnings={result['warnings']}",flush=True)
            except Exception as exc:
                failures.append({"lecture_number":item["lecture_number"],"url":item["url"],"error":str(exc)})
                print(f"ERROR {item['lecture_number']:02}: {exc}",file=sys.stderr,flush=True)
            manifest = {"schema_version":SCHEMA_VERSION,"generated_at":now(),"index_url":args.index_url,"inventory_file":"inventory.json","normalization":index["normalization"],"expected_count":60,"archived_count":len(archived),"failures":failures,"lectures":[archived[number] for number in sorted(archived)]}
            write_json(manifest_path,manifest)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
