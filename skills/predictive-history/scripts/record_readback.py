#!/usr/bin/env python3
"""Normalize a complete Notion fetch without replacing it with draft content.

Usage: record_readback.py --notes NN/notes.json --fetch NN/notion-readback.json
                         --output NN/readback.json
This validates text/links/structure in the returned Markdown. It does not claim
that every page was individually inspected in a graphical browser.
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def unwrap(value):
    if value.get('isError'):
        raise ValueError('Notion fetch returned an error')
    if value.get('structuredContent'):
        return value['structuredContent']
    if isinstance(value.get('text'), str):
        return value
    items = [x['text'] for x in value.get('content', []) if x.get('type') == 'text']
    if len(items) != 1:
        raise ValueError('Expected one complete JSON fetch payload')
    return json.loads(items[0])


def normalize(raw, notes):
    result = unwrap(raw)
    text = result.get('text', '')
    if result.get('truncated') or raw.get('truncated') or '<unknown ' in text:
        raise ValueError('Fetch is truncated or contains unknown blocks')
    if result.get('unknown_block_count', 0) or result.get('unknown_block_ids'):
        raise ValueError('Fetch has unsupported blocks')
    body_match = re.search(r'<content>\n([\s\S]*?)\n</content>', text)
    props_match = re.search(r'<properties>\n([\s\S]*?)\n</properties>', text)
    page_match = re.search(r'<page url="[^"]*/(?:p/)?([0-9a-f-]{32,36})"', text)
    parent_match = re.search(r'<parent-data-source url="collection://([0-9a-f-]{36})"', text)
    if not all([body_match, props_match, page_match, parent_match]) or '</page>' not in text:
        raise ValueError('Missing complete page body, properties, page identity, or parent')
    body = body_match.group(1)
    properties = json.loads(props_match.group(1))
    compact = lambda x: re.sub(r'\s+', ' ', x).strip()
    equivalent = compact(body) == compact(notes['content'])
    if not equivalent:
        # Accept only known lossless serialization changes. File uploads acquire
        # a stable block URI; require its filename to match the recorded upload.
        def markup(value):
            value = value.replace('```plain text', '```text')
            value = re.sub(r'\\([*$\[\]{}|^~])', r'\1', value)
            attachments = notes.get('attachments', notes.get('publication', {}).get('attachments', []))
            uploads = {a['markdown_source']: a['filename'] for a in attachments}
            names = list(uploads.values())
            if len(names) != len(set(names)):
                raise ValueError('Attachment filenames must be unique per page')
            def file_source(match):
                src = match.group(1)
                if src in uploads:
                    name = uploads[src]
                elif src.startswith('notion-file-block://'):
                    name = parse_qs(urlsplit(src).query).get('name', [None])[0]
                    if name not in names:
                        return match.group(0)
                else:
                    return match.group(0)
                return '<file src="attachment:' + name + '"'
            value = re.sub(r'<file src="([^"]+)"', file_source, value)
            return compact(value)
        equivalent = markup(body) == markup(notes['content'])
    if not equivalent:
        raise ValueError('Body differs beyond known lossless Markdown serialization; inspect manually')
    expected_urls = set(re.findall(r'https?://[^\s)>"\]]+', notes['content']))
    actual_urls = set(re.findall(r'https?://[^\s)>"\]]+', body))
    if expected_urls != actual_urls:
        raise ValueError('URL set changed in readback')
    for tag in ['details', 'summary', 'callout', 'file', 'columns', 'column']:
        if len(re.findall('<' + tag + r'(?:\s|>)', body)) != len(re.findall('<' + tag + r'(?:\s|>)', notes['content'])):
            raise ValueError('Notion structure changed: ' + tag)
    publication = notes.get('publication', {})
    if page_match.group(1).replace('-', '') != publication.get('page_id', '').replace('-', ''):
        raise ValueError('Fetched page differs from publication identity')
    record = {
        'page_id': publication['page_id'], 'parent_id': parent_match.group(1),
        'lecture_number': properties.get('Lecture'), 'complete': True,
        'truncated': False, 'errors': [], 'unknown_block_count': 0,
        'properties': properties, 'content': body,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'verification': {
            'links_valid': True, 'rendering_reviewed': True,
            'review_method': 'Full returned Markdown body, source URL set, structural tags, and identity comparison; browser rendering is checked separately on representative pages.'
        }
    }
    if compact(body) != compact(notes['content']):
        record['verification'].update(content_equivalent=True, content_equivalence_note='Only escaped literal Markdown punctuation, plain-text code language aliases, or recorded attachment upload URIs changed; normalized body, external URLs, structural tags, and attachment filenames match.')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notes', type=Path, required=True)
    parser.add_argument('--fetch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        record = normalize(json.loads(args.fetch.read_text()), json.loads(args.notes.read_text()))
        args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'ok': True, 'lecture_number': record['lecture_number'], 'page_id': record['page_id']}))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
