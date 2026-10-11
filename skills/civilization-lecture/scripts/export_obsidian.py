#!/usr/bin/env python3
"""Convert the supported study-page Markdown to native, portable Obsidian notes.

This deliberately fails on unknown Notion blocks or unmapped page/file references.
Callers must back up the destination, reconcile live edits, and supply exact maps.
No vault cleanup or remote publishing is performed by this module.
"""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path


def filename(title):
    return re.sub(r'[\\/:*?"<>|\[\]#^]', ' — ', title).strip().rstrip('.')


def frontmatter(properties):
    """JSON scalar/list values are valid YAML and avoid accidental YAML coercion."""
    return '---\n' + '\n'.join(f'{k}: {json.dumps(v, ensure_ascii=False)}' for k, v in properties.items()) + '\n---\n\n'


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = []
        elif tag in ('td', 'th'):
            if any(k in ('rowspan', 'colspan') and v != '1' for k, v in attrs):
                raise ValueError('Spanning table cells require manual conversion')
            self.cell = []
        elif tag == 'br' and self.cell is not None:
            self.cell.append('<br>')
        elif tag not in ('table',):
            raise ValueError('Unsupported nested table markup: ' + tag)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.row.append(' '.join(''.join(self.cell).split()).replace('|', '\\|'))
            self.cell = None
        elif tag == 'tr':
            self.rows.append(self.row)
            self.row = None


def markdown_table(value):
    parser = TableParser()
    parser.feed(value)
    rows = parser.rows
    if not rows or len({len(r) for r in rows}) != 1:
        raise ValueError('Empty or irregular table')
    rows.insert(1, ['---'] * len(rows[0]))
    return '\n'.join('| ' + ' | '.join(r) + ' |' for r in rows)


def space_blocks(body):
    """Restore block boundaries omitted by Notion's compact fetch serializer."""
    out, in_fence = [], False
    for line in body.splitlines():
        line = line.lstrip('\t')
        previous = out[-1] if out else ''
        if line and previous and not in_fence:
            same_quote = line.startswith('>') and previous.startswith('>')
            same_list = bool(re.match(r'(?:[-*]|\d+\.) ', line) and re.match(r'(?:[-*]|\d+\.) ', previous))
            same_table = line.startswith('|') and previous.startswith('|')
            if not (same_quote or same_list or same_table):
                out.append('')
        out.append(line)
        if line.startswith('```'):
            in_fence = not in_fence
    return '\n'.join(out)


def callout(title, body, kind='info', collapsed=True):
    # Blank quote lines retain paragraphs and tables inside the callout.
    title = re.sub(r'\s+', ' ', title).strip()
    lines = space_blocks(body.strip()).splitlines()
    return f'> [!{kind}]' + ('- ' if collapsed else ' ') + title + '\n' + '\n'.join('> ' + l if l else '>' for l in lines)


def convert(body, *, pages, images, files):
    """Maps: compact page UUID -> wiki target; URL/file URI -> local wiki target."""
    body = re.sub(r'<table\b[^>]*>[\s\S]*?</table>', lambda m: markdown_table(m[0]), body)

    def page(match):
        key = match[1].rstrip('/').split('/')[-1].replace('-', '')
        if key not in pages:
            raise ValueError('Unmapped Notion page: ' + key)
        target = pages[key]
        return '[[' + target + '|' + target.rsplit('/', 1)[-1] + ']]'

    body = re.sub(r'<mention-page url="([^"]+)"\s*/>', page, body)

    def picture(match):
        caption, url = match.groups()
        if url not in images:
            raise ValueError('Image has not been archived: ' + url)
        return '![[%s]]\n\n*%s*' % (images[url], caption)

    body = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', picture, body)

    def attachment(match):
        uri = html.unescape(match[1])
        if uri not in files:
            raise ValueError('Unmapped attachment: ' + uri)
        return callout('Source record', '![[%s]]' % files[uri], collapsed=True)

    body = re.sub(r'<file src="([^"]+)"[^>]*>[\s\S]*?</file>', attachment, body)

    def columns(match):
        children = re.findall(r'<column\b[^>]*>([\s\S]*?)</column>', match[1])
        if not children:
            raise ValueError('Empty columns')
        # Nested figure callouts give each caption its own responsive grid cell.
        cells = []
        for child in children:
            child = '\n'.join(l.lstrip('\t') for l in child.strip().splitlines())
            cells.append(callout('', child, kind='figure', collapsed=False))
        return callout('Figures', '\n\n'.join(cells), kind='gallery', collapsed=False)

    body = re.sub(r'<columns>\s*([\s\S]*?)\s*</columns>', columns, body)
    # Innermost first, so nested details remain nested native callouts.
    pattern = r'<details>\s*<summary>(.*?)</summary>((?:(?!<details>)[\s\S])*?)</details>'
    while re.search(pattern, body):
        def detail(match):
            child = '\n'.join(l[1:] if l.startswith('\t') else l for l in match[2].strip('\n').splitlines())
            title = match[1]
            kind = 'question' if re.search(r'answer|cue|\?', title, re.I) else 'info'
            return callout(title, child, kind=kind)
        body = re.sub(pattern, detail, body)
    body = re.sub(r'<callout\b[^>]*>([\s\S]*?)</callout>', lambda m: callout('', '\n'.join(l.lstrip('\t') for l in m[1].strip().splitlines()), collapsed=False), body)
    body = re.sub(r'```plain text\b', '```text', body)
    body = body.replace('<empty-block/>', '')
    outside_code = re.sub(r'```[\s\S]*?```', '', body)
    if re.search(r'</?(?!br\b)[a-z][a-z0-9-]*(?:\s[^>]*)?/?>', outside_code, re.I):
        raise ValueError('Unconverted Notion markup')
    return re.sub(r'\n{3,}', '\n\n', space_blocks(body)).strip() + '\n'


def validate_wikilinks(root):
    """Return broken/ambiguous targets; resolve vault-relative targets first."""
    root = Path(root)
    all_files = [p for p in root.rglob('*') if p.is_file() and '.obsidian' not in p.parts]
    errors = []
    for p in all_files:
        if p.suffix != '.md':
            continue
        for target in re.findall(r'!?\[\[([^\]]+)\]\]', p.read_text()):
            reference = target.split('|')[0]
            target, _, fragment = reference.partition('#')
            direct = [root / target, root / (target + '.md')]
            matches = [x for x in direct if x.is_file()]
            if not matches:
                matches = [x for x in all_files if x.name == target or x.stem == target]
            if len(set(matches)) != 1:
                errors.append({'note': str(p.relative_to(root)), 'target': target, 'matches': len(matches)})
            elif fragment and matches[0].suffix == '.md':
                text = matches[0].read_text()
                headings = re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.M)
                if fragment.startswith('^'):
                    valid = bool(re.search(r'\^' + re.escape(fragment[1:]) + r'\s*$', text, re.M))
                else:
                    valid = fragment.casefold() in {h.casefold() for h in headings}
                if not valid:
                    errors.append({'note': str(p.relative_to(root)), 'target': reference, 'error': 'missing fragment'})
    return errors
