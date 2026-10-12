#!/usr/bin/env python3
"""Audit a private course against its complete inventory and publication records.

This rechecks complete stored fetch responses. It does not contact Notion or
certify historical truth, visual interpretation, or live external availability.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

from record_readback import normalize
from validate_notes import load_object, normalized_url, validate
from course_config import inventory_entries, load_course, url_key


def audit_course(root, published=False, navigation=False):
    errors, warnings, records = [], [], {}
    totals = {'lectures': 0, 'source_words': 0, 'source_blocks': 0,
              'source_figures': 0, 'embedded_figures': 0, 'source_tables': 0,
              'source_fragments': 0, 'attachments': 0, 'note_words': 0}
    root = Path(root)
    try:
        inventory = load_object(root / 'inventory.json')
        entries = inventory_entries(inventory)
        course = load_course(root / 'course.json', 'notion' if published else None) if (root / 'course.json').exists() else None
        if course and inventory.get('course_id', 'civilization') != course['course_id']:
            raise ValueError('Inventory belongs to a different course')
        if inventory.get('course_id') and not course:
            raise ValueError('Course profile is missing')
        if not course:
            warnings.append('Legacy archive: no course profile; no configured destination isolation check')
        if (root / 'manifest.json').exists():
            manifest = load_object(root / 'manifest.json')
            archived = manifest.get('lectures', [])
            if manifest.get('failures'):
                errors.append('Extraction manifest contains unresolved failures')
            if manifest.get('expected_count') != len(entries) or manifest.get('archived_count') != len(entries):
                errors.append('Extraction manifest is incomplete for this course inventory')
            expected = {(e['lecture_number'], url_key(e['url'])) for e in entries}
            actual = {(e['lecture_number'], url_key(e['url'])) for e in archived}
            if len(archived) != len(entries) or actual != expected:
                errors.append('Extraction manifest source identities differ from the complete inventory')
            if manifest.get('course_id', 'civilization') != inventory.get('course_id', 'civilization'):
                errors.append('Extraction manifest belongs to a different course')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {'ok': False, 'counts': totals, 'errors': [str(exc)], 'warnings': warnings}
    for entry in entries:
        number = entry['lecture_number']
        folder = root / entry['directory']
        try:
            source = load_object(folder / 'source.json')
            notes = load_object(folder / 'notes.json')
            readback = normalize(load_object(folder / 'notion-readback.json'), notes) if published else None
            result = validate(source, notes, folder / 'source.json', readback=readback, require_published=published)
            errors.extend(f'{number:02d}: {e}' for e in result['errors'])
            warnings.extend(f'{number:02d}: {w}' for w in result['warnings'])
            if source.get('lecture_number') != number:
                errors.append(f'{number:02d}: source stored in wrong directory')
            if url_key(source['source_url']) != url_key(entry['url']):
                errors.append(f'{number:02d}: source URL differs from course inventory')
            if source.get('source_label') != entry.get('source_label'):
                errors.append(f'{number:02d}: source label differs from course inventory')
            if course and source.get('course_id', 'civilization') != course['course_id']:
                errors.append(f'{number:02d}: source belongs to a different course')
            if course and published:
                parent = course['destinations']['notion']['lecture_parent_id']
                if notes.get('publication', {}).get('parent_id', '').replace('-', '') != parent.replace('-', ''):
                    errors.append(f'{number:02d}: publication is outside this course destination')
            records[number] = (source, notes)
            totals['lectures'] += 1
            for key, source_key in [('source_words', 'words'), ('source_blocks', 'blocks'),
                                    ('source_figures', 'figures'), ('source_tables', 'tables')]:
                totals[key] += source['counts'][source_key]
            totals['embedded_figures'] += sum(f.get('disposition') == 'embedded' for f in notes['figures'])
            totals['attachments'] += len(notes.get('attachments', notes.get('publication', {}).get('attachments', [])))
            totals['note_words'] += result['counts']['content_words']
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{number:02d}: {exc}')

    sources = {}
    for source, _ in records.values():
        ids = {unquote(h['source_id']) for h in source.get('headings', []) if h.get('source_id')}
        for key in ['source_url', 'canonical_url']:
            if source.get(key):
                sources[normalized_url(source[key])] = ids
    page_ids = [(n.get('publication', {}).get('page_id') or '').replace('-', '').lower() for _, n in records.values()]
    if published and ('' in page_ids or len(page_ids) != len(set(page_ids))):
        errors.append('Missing or duplicate published page identities')
    source_urls = [normalized_url(s['source_url']) for s, _ in records.values()]
    if len(source_urls) != len(set(source_urls)):
        errors.append('Duplicate lecture source URLs')
    canonical_urls = [normalized_url(s.get('canonical_url') or s['source_url']) for s, _ in records.values()]
    if len(canonical_urls) != len(set(canonical_urls)):
        errors.append('Duplicate canonical source identities; reconcile redirected or variant articles')
    for number, (_, notes) in records.items():
        for url in re.findall(r'https?://[^\s)>"\]]+', notes['content']):
            parts = urlsplit(url)
            key = normalized_url(urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, '')))
            if key in sources and parts.fragment:
                totals['source_fragments'] += 1
                if unquote(parts.fragment) not in sources[key]:
                    errors.append(f'{number:02d}: unknown public source fragment: {url}')
        if navigation:
            expected = {}
            for label, neighbor in [('previous', number - 1), ('next', number + 1)]:
                if 1 <= neighbor <= len(entries):
                    expected[label] = records.get(neighbor, ({}, {}))[1].get('publication', {}).get('page_id')
            nav = notes.get('navigation', {})
            for label, page_id in expected.items():
                if not page_id or nav.get(label) != page_id:
                    errors.append(f'{number:02d}: incorrect {label} lecture navigation')
                elif page_id.replace('-', '') not in notes['content'].replace('-', ''):
                    errors.append(f'{number:02d}: {label} target is absent from page body')
            if (number == 1 and nav.get('previous')) or (number == len(entries) and nav.get('next')):
                errors.append(f'{number:02d}: navigation points outside the course')
    return {'ok': not errors, 'course_id': inventory.get('course_id', 'civilization'), 'expected_count': len(entries), 'counts': totals, 'errors': errors, 'warnings': warnings,
            'review_boundary': 'Stored-source and publication consistency; not a comprehensive historical fact-check or a live URL-availability test.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--require-published', action='store_true')
    p.add_argument('--require-navigation', action='store_true')
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    result = audit_course(args.archive, args.require_published, args.require_navigation)
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        args.report.write_text(output)
    print(output, end='')
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
