#!/usr/bin/env python3
"""Convert a reviewed subset of Notion enhanced Markdown to Obsidian.

This is not a Notion API block converter. It accepts explicit page/asset maps,
fails on unknown markup or references, and never writes a vault or fetches data.
Callers own full retrieval, asset archival, backups, and user-edit reconciliation.
"""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, unquote, urlsplit


def filename(title):
    result = re.sub(r'[\\/:*?"<>|\[\]#^\x00-\x1f]', ' — ', title).strip().rstrip('.')
    if not result or result in ('.', '..'):
        raise ValueError('A note needs a nonempty filename')
    return result


def frontmatter(properties):
    """JSON keys and values are YAML-compatible and avoid accidental coercion."""
    return '---\n' + '\n'.join(f'{json.dumps(str(k), ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}' for k, v in properties.items()) + '\n---\n\n'


def _line_parts(line):
    return re.match(r'([ \t]*(?:>[ \t]*)*)(.*)', line).groups()


def _fence(content):
    return re.match(r'(`{3,}|~{3,})(.*)$', content)


class _Literals:
    """Mask code and escaped punctuation while retaining line/container structure."""
    def __init__(self):
        self.values = {}

    def save(self, value, kind='literal'):
        token = f'\x00notion-{kind}-{len(self.values)}\x00'
        self.values[token] = value
        return token

    def multiline(self, value):
        return '\n'.join(prefix + self.save(content) for prefix, content in
                         (re.match(r'([ \t]*)(.*)', line).groups() for line in value.split('\n')))

    def protect_inline(self, text):
        out, pos = [], 0
        while pos < len(text):
            if text[pos] == '\\' and pos + 1 < len(text) and text[pos + 1] in r'\`*_{}[]<>()!#+-.|>':
                out.append(self.save(text[pos:pos + 2]))
                pos += 2
            elif text[pos] == '`':
                ticks = re.match(r'`+', text[pos:])[0]
                close = re.search(r'(?<!`)' + re.escape(ticks) + r'(?!`)', text[pos + len(ticks):])
                if close:
                    end = pos + len(ticks) + close.end()
                    out.append(self.multiline(text[pos:end]))
                    pos = end
                else:
                    out.append(ticks)
                    pos += len(ticks)
            else:
                out.append(text[pos])
                pos += 1
        return ''.join(out)

    def protect(self, text):
        if '\x00' in text:
            raise ValueError('NUL characters are unsupported in Markdown')
        out, plain, active = [], [], None

        def flush():
            if plain:
                out.append(self.protect_inline(''.join(plain)))
                plain.clear()

        for line in text.splitlines(keepends=True):
            newline = '\n' if line.endswith('\n') else ''
            prefix, content = _line_parts(line.rstrip('\n'))
            match = _fence(content)
            depth = prefix.count('>')
            if active:
                closing = (match and match[1][0] == active[0] and len(match[1]) >= active[1]
                           and not match[2].strip() and depth == active[2])
                out.append(prefix + self.save(content, 'fence-end' if closing else 'fence-body') + newline)
                if closing:
                    active = None
            elif match:
                flush()
                active = (match[1][0], len(match[1]), depth)
                out.append(prefix + self.save(content, 'fence-start') + newline)
            else:
                plain.append(line)
        flush()
        return ''.join(out)

    def restore(self, text):
        return re.sub(r'\x00notion-[a-z-]+-\d+\x00', lambda m: self.values[m[0]], text)


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            if self.row is not None:
                raise ValueError('Nested table rows require manual conversion')
            self.row = []
        elif tag in ('td', 'th'):
            if self.row is None or self.cell is not None:
                raise ValueError('Malformed table cells')
            if any(k in ('rowspan', 'colspan') and v != '1' for k, v in attrs):
                raise ValueError('Spanning table cells require manual conversion')
            self.cell = []
        elif tag == 'br' and self.cell is not None:
            self.cell.append('<br>')
        elif tag not in ('table', 'thead', 'tbody', 'tfoot'):
            raise ValueError('Unsupported nested table markup: ' + tag)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            if self.row is None or self.cell is None:
                raise ValueError('Malformed table cells')
            self.row.append(' '.join(''.join(self.cell).split()).replace('|', '\\|'))
            self.cell = None
        elif tag == 'tr':
            if self.row is None or self.cell is not None:
                raise ValueError('Malformed table row')
            self.rows.append(self.row)
            self.row = None


def markdown_table(value):
    parser = TableParser()
    parser.feed(value)
    rows = parser.rows
    if parser.row is not None or parser.cell is not None or not rows or not rows[0] or len({len(r) for r in rows}) != 1:
        raise ValueError('Empty or irregular table')
    rows.insert(1, ['---'] * len(rows[0]))
    return '\n'.join('| ' + ' | '.join(r) + ' |' for r in rows)


def space_blocks(body):
    """Separate callouts/structural blocks without rewriting prose or list indents."""
    out, active = [], None
    for line in body.splitlines():
        previous = out[-1] if out else ''
        quote, content = _line_parts(line)
        depth = quote.count('>')
        fence = _fence(content)
        masked_start = content.startswith('\x00notion-fence-start-')
        masked_end = content.startswith('\x00notion-fence-end-')
        in_fence = active is not None
        if line and previous and not in_fence:
            previous_quote, previous_content = _line_parts(previous)
            previous_depth = previous_quote.count('>')
            same_quote = depth > 0 and previous_depth > 0
            same_table = content.startswith('|') and previous_content.startswith('|')
            new_callout = bool(re.match(r'\[![\w-]+\][+-]?(?:\s|$)', content))
            if same_quote and new_callout and previous_content.strip() and previous_depth >= depth:
                out.append(('> ' * (depth - 1)).rstrip())
            elif same_quote and content.strip() and previous_content.strip() and previous_depth > depth:
                out.append(('> ' * depth).rstrip())
            elif not same_quote and (depth != previous_depth or
                    (not same_table and (content.startswith('|') or previous_content.startswith('|'))) or
                    re.match(r'#{1,6}\s', content) or re.match(r'#{1,6}\s', previous_content) or
                    fence or masked_start or previous_content.startswith('\x00notion-fence-end-')):
                out.append('')
        out.append(line)
        if masked_start:
            active = ('masked', 0, depth)
        elif masked_end:
            active = None
        elif fence:
            if not in_fence:
                active = (fence[1][0], len(fence[1]), depth)
            elif (fence[1][0] == active[0] and len(fence[1]) >= active[1]
                  and not fence[2].strip() and depth == active[2]):
                active = None
    return '\n'.join(out)


def callout(title, body, kind='info', collapsed=True):
    title = re.sub(r'\s+', ' ', title).strip()
    lines = space_blocks(body.strip('\n')).splitlines()
    return f'> [!{kind}]' + ('- ' if collapsed else ' ') + title + '\n' + '\n'.join('> ' + l if l else '>' for l in lines)


def _dedent_container(text):
    """Remove only common serializer indentation, preserving nested list structure."""
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    nonempty = [line for line in lines if line.strip()]
    if not nonempty:
        return ''
    indents = [re.match(r'[ \t]*', line)[0] for line in nonempty]
    common = indents[0]
    for indent in indents[1:]:
        while not indent.startswith(common):
            common = common[:-1]
    return '\n'.join(line[len(common):] if line.startswith(common) else line for line in lines)


def _is_notion_url(value):
    parsed = urlsplit(value)
    host = (parsed.hostname or '').lower()
    return parsed.scheme in ('http', 'https') and (host in ('notion.so', 'notion.com', 'notion.site') or
           host.endswith(('.notion.so', '.notion.com', '.notion.site')))


def notion_page_id(value):
    """Normalize UUIDs and common Notion page URLs; retain legacy short map keys."""
    value = html.unescape(str(value)).strip()
    if '://' not in value:
        return value.replace('-', '').lower()
    if not _is_notion_url(value):
        raise ValueError('Expected a Notion page URL: ' + value)
    parsed = urlsplit(value)
    last = unquote(parsed.path.rstrip('/').rsplit('/', 1)[-1])
    match = re.search(r'([0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$', last, re.I)
    if match:
        return match[1].replace('-', '').lower()
    if parse_qs(parsed.query).get('p'):
        return notion_page_id(parse_qs(parsed.query)['p'][0])
    return last.replace('-', '').lower()


def _wiki_target(value):
    if not isinstance(value, str) or not value or any(c in value for c in '|[]\n\r\x00\\'):
        raise ValueError('Unsafe wiki target: ' + repr(value))
    path = value.split('#', 1)[0]
    if not path or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts or re.match(r'^[a-zA-Z]:', path):
        raise ValueError('Unsafe wiki target: ' + value)
    return value


def _attributes(value):
    return {key: html.unescape(quoted[1:-1]) for key, quoted in
            re.findall(r'([\w-]+)\s*=\s*("[^"]*"|\'[^\']*\')', value)}


def _replace_blocks(pattern, replacement, body):
    """Keep the serializer's containing indent on every generated block line."""
    def replace(match):
        prefix = body[body.rfind('\n', 0, match.start()) + 1:match.start()]
        result = replacement(match)
        if not prefix.strip():
            result = result.replace('\n', '\n' + prefix)
        return result
    return re.sub(pattern, replace, body)


def convert(body, *, pages, images, files, external_pages=None, file_labels=None, attachment_label='Source record'):
    """Convert supported enhanced Markdown with exact, caller-verified maps.

    pages: Notion ID/URL -> vault-relative wiki target. images/files: source URI
    -> archived local target. external_pages: verified Notion ID/URL -> web URL
    for references intentionally kept outside the export. file_labels overrides
    attachment callout titles; attachment_label retains the legacy default.
    Notion block anchors need an explicit external mapping (no inferred headings).
    """
    pages = {notion_page_id(key): _wiki_target(value) for key, value in pages.items()}
    external_pages = {notion_page_id(key): value for key, value in (external_pages or {}).items()}
    for key, url in external_pages.items():
        if not _is_notion_url(url) or notion_page_id(url) != key:
            raise ValueError('External page URL does not match its verified identity: ' + str(url))
    images = {html.unescape(key): _wiki_target(value) for key, value in images.items()}
    files = {html.unescape(key): _wiki_target(value) for key, value in files.items()}
    literals = _Literals()
    body = literals.protect(body)

    def page_link(url, label=None):
        url = html.unescape(url)
        key = notion_page_id(url)
        if key in pages and not urlsplit(url).fragment:
            target = pages[key]
            label = label or target.split('#', 1)[0].rsplit('/', 1)[-1]
            return '[[' + target + '|' + label.replace('|', '\\|') + ']]'
        if key in external_pages:
            target = external_pages[key]
            if urlsplit(url).fragment:
                target = target.split('#', 1)[0] + '#' + urlsplit(url).fragment
            return '[' + (label or 'Notion page') + '](' + target + ')'
        if key in pages:
            raise ValueError('Notion block anchor needs an explicit external mapping: ' + url)
        raise ValueError('Unmapped Notion page: ' + key)

    def mention(match):
        attrs = _attributes(match[1])
        if 'url' not in attrs:
            raise ValueError('Page mention is missing its URL')
        return page_link(attrs['url'], attrs.get('title'))

    body = re.sub(r'<mention-page\b([^>]*)/\s*>', mention, body)

    def markdown_link(match):
        label, url, title = match.groups()
        url = url.strip('<>')
        if not _is_notion_url(html.unescape(url)):
            return match[0]
        if title:
            raise ValueError('Notion link hover titles require manual conversion')
        return page_link(url, label)

    body = re.sub(r'(?<!!)\[([^\]\n]*)\]\((<[^>\n]+>|[^\s)]+)(?:[ \t]+("[^"]*"|\'[^\']*\'))?\)', markdown_link, body)

    def picture(match):
        caption, url = match.groups()
        url = html.unescape(url)
        if url not in images:
            raise ValueError('Image has not been archived: ' + url)
        return '![[%s]]' % images[url] + ('\n\n*%s*' % caption if caption else '')

    body = _replace_blocks(r'!\[([^\]\n]*)\]\(([^\s)]+)\)', picture, body)

    def attachment(match):
        attrs = _attributes(match[1])
        uri = attrs.get('src', '')
        if uri not in files:
            raise ValueError('Unmapped attachment: ' + uri)
        label = (file_labels or {}).get(uri, attachment_label)
        caption = match[2].strip()
        content = '![[%s]]' % files[uri] + ('\n\n' + caption if caption else '')
        return callout(label, content, collapsed=True)

    body = _replace_blocks(r'<file\b([^>]*)>([\s\S]*?)</file>', attachment, body)
    def table(match):
        value = match[0]
        # Markdown table delimiters must be escaped even inside a code span.
        for token in re.findall(r'\x00notion-[a-z-]+-\d+\x00', value):
            literal = literals.values[token]
            if '|' in literal:
                value = value.replace(token, literals.save(literal.replace('|', '\\|')))
        return markdown_table(value)

    body = _replace_blocks(r'<table\b[^>]*>[\s\S]*?</table>', table, body)

    def columns(match):
        children = re.findall(r'<column\b[^>]*>([\s\S]*?)</column>', match[1])
        if not children or re.sub(r'<column\b[^>]*>[\s\S]*?</column>', '', match[1]).strip():
            raise ValueError('Empty or unsupported columns')
        cells = [callout('', _dedent_container(child), kind='figure', collapsed=False) for child in children]
        return callout('Figures', '\n\n'.join(cells), kind='gallery', collapsed=False)

    body = _replace_blocks(r'<columns>\s*([\s\S]*?)\s*</columns>', columns, body)
    pattern = r'<details>\s*<summary>(.*?)</summary>((?:(?!<details>)[\s\S])*?)</details>'
    while re.search(pattern, body):
        def detail(match):
            title = match[1]
            kind = 'question' if re.search(r'answer|cue|\?', title, re.I) else 'info'
            return callout(title, _dedent_container(match[2]), kind=kind)
        body = _replace_blocks(pattern, detail, body)
    pattern = r'<callout\b[^>]*>((?:(?!<callout\b)[\s\S])*?)</callout>'
    while re.search(pattern, body):
        body = _replace_blocks(pattern, lambda m: callout('', _dedent_container(m[1]), collapsed=False), body)
    body = body.replace('<empty-block/>', '')
    if re.search(r'</?(?!br\b)[a-z][a-z0-9-]*(?:\s[^>]*)?/?>', body, re.I):
        raise ValueError('Unconverted Notion markup')
    if re.search(r'!\[', body.replace('![[', '')):
        raise ValueError('Unsupported image Markdown requires manual conversion')
    return literals.restore(re.sub(r'\n{3,}', '\n\n', space_blocks(body)).strip()) + '\n'


def validate_wikilinks(root):
    """Audit active wiki references, excluding code and escaped examples.

    Resolve vault paths first, then note-relative paths and unique bare filenames.
    Same-note headings/block IDs are supported; escaping the vault is an error.
    """
    root = Path(root).resolve()
    all_files = [p for p in root.rglob('*') if p.is_file() and '.obsidian' not in p.relative_to(root).parts]
    errors = []
    for p in all_files:
        if p.suffix != '.md' or not p.resolve().is_relative_to(root):
            continue
        literals = _Literals()
        text = literals.protect(p.read_text())
        for found in re.findall(r'!?\[\[([^\]]+)\]\]', text):
            reference = literals.restore(found).replace('\\|', '|').split('|', 1)[0]
            target, _, fragment = reference.partition('#')
            error = {'note': str(p.relative_to(root)), 'target': reference}
            if '\\' in target or PurePosixPath(target).is_absolute() or re.match(r'^[a-zA-Z]:', target):
                errors.append({**error, 'error': 'unsafe path'})
                continue
            if not target:
                matches = [p]
            else:
                relative = target.startswith(('./', '../'))
                base = p.parent if relative else root
                direct = [base / target, base / (target + '.md')]
                if any(not candidate.resolve().is_relative_to(root) for candidate in direct):
                    errors.append({**error, 'error': 'unsafe path'})
                    continue
                matches = [candidate for candidate in direct if candidate.is_file()]
                if not matches and not relative:
                    matches = [candidate for candidate in [p.parent / target, p.parent / (target + '.md')]
                               if candidate.is_file() and candidate.resolve().is_relative_to(root)]
                if not matches and '/' not in target:
                    matches = [candidate for candidate in all_files if candidate.name == target or candidate.stem == target]
            matches = list({candidate.resolve() for candidate in matches})
            if any(not candidate.is_relative_to(root) for candidate in matches):
                errors.append({**error, 'error': 'unsafe path'})
            elif len(matches) != 1:
                errors.append({**error, 'matches': len(matches)})
            elif fragment and matches[0].suffix == '.md':
                target_literals = _Literals()
                target_text = target_literals.protect(matches[0].read_text())
                headings = [target_literals.restore(heading) for heading in
                            re.findall(r'^#{1,6}\s+(.+?)\s*#*$', target_text, re.M)]
                if fragment.startswith('^'):
                    valid = bool(re.search(r'\^' + re.escape(fragment[1:]) + r'\s*$', target_text, re.M))
                else:
                    valid = unquote(fragment).casefold() in {heading.casefold() for heading in headings}
                if not valid:
                    errors.append({**error, 'error': 'missing fragment'})
    return errors
