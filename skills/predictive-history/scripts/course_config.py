#!/usr/bin/env python3
"""Validate private course profiles and isolation between course destinations."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit, urlunsplit


def url_key(value):
    parts = urlsplit(value)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'), parts.query, ''))


def validate_course(course, destinations=None):
    if course.get('schema_version') != 1:
        raise ValueError('course.schema_version must be 1')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', course.get('course_id', '')):
        raise ValueError('course_id must be a lowercase slug')
    for key in ('title', 'title_prefix', 'index_url'):
        if not isinstance(course.get(key), str) or not course[key].strip():
            raise ValueError('course.' + key + ' is required')
    if urlsplit(course['index_url']).scheme not in ('http', 'https'):
        raise ValueError('index_url must be an HTTP(S) URL')
    order = course.get('order')
    if order is not None:
        if not isinstance(order, list) or not order or not all(isinstance(x, str) and urlsplit(x).scheme in ('http', 'https') for x in order):
            raise ValueError('order must be a nonempty list of source URLs')
        if len({url_key(x) for x in order}) != len(order):
            raise ValueError('order contains duplicate source URLs')
    dest = course.get('destinations', {})
    notion, obsidian = dest.get('notion', {}), dest.get('obsidian', {})
    if destinations in ('notion', 'both') or notion:
        if not all(isinstance(notion.get(k), str) and notion[k].strip() for k in ('root_id', 'lecture_parent_id')):
            raise ValueError('Notion destination requires root_id and lecture_parent_id from the actual schema')
        if any(not re.fullmatch(r'[0-9a-fA-F]{32}', notion[k].replace('-', '')) for k in ('root_id', 'lecture_parent_id')):
            raise ValueError('Notion destinations must be actual UUIDs, not placeholder text or page titles')
    if destinations in ('obsidian', 'both') or obsidian:
        vault, folder = obsidian.get('vault', ''), obsidian.get('folder', '')
        if not vault or not Path(vault).expanduser().is_absolute():
            raise ValueError('Obsidian destination requires an absolute vault path')
        if not folder or PurePosixPath(folder).is_absolute() or any(x in ('', '.', '..') for x in folder.split('/')) or '\\' in folder:
            raise ValueError('Obsidian folder must be a nonempty vault-relative folder without traversal')
    return course


def load_course(path, destinations=None):
    return validate_course(json.loads(Path(path).read_text()), destinations)


def check_isolation(courses):
    """Reject reused Notion roots/parents and overlapping folders in one vault."""
    ids, notion_ids, folders = set(), {}, []
    for c in courses:
        validate_course(c)
        identity = c['course_id']
        if identity in ids:
            raise ValueError('Duplicate course_id: ' + identity)
        ids.add(identity)
        dest = c.get('destinations', {})
        notion = dest.get('notion', {})
        for value in {notion[k] for k in ('root_id', 'lecture_parent_id') if k in notion}:
            key = value.replace('-', '').lower()
            if key in notion_ids:
                raise ValueError('Notion destination shared by ' + notion_ids[key] + ' and ' + identity)
            notion_ids[key] = identity
        obs = dest.get('obsidian')
        if obs:
            vault = Path(obs['vault']).expanduser().resolve()
            path = (vault / obs['folder']).resolve()
            if path == vault or vault not in path.parents:
                raise ValueError('Course folder resolves outside the vault')
            for other, previous in folders:
                # casefold also protects the usual case-insensitive macOS volume.
                a, b = str(path).casefold(), str(previous).casefold()
                if a == b or a.startswith(b + '/') or b.startswith(a + '/'):
                    raise ValueError('Obsidian folders overlap: ' + other + ' and ' + identity)
            folders.append((identity, path))


def inventory_entries(inventory):
    entries = inventory.get('lectures', [])
    if not entries or inventory.get('lecture_count') != len(entries):
        raise ValueError('Incomplete or empty inventory')
    if inventory.get('integrity', {}).get('pagination_terminated') is not True:
        raise ValueError('Inventory pagination is not complete')
    if inventory.get('advertised_lecture_count') not in (None, len(entries)):
        raise ValueError('Inventory disagrees with advertised count')
    seen = {'urls': set(), 'directories': set()}
    for ordinal, entry in enumerate(entries, 1):
        if entry.get('lecture_number') != ordinal:
            raise ValueError('Inventory ordinals must be unique and ordered from 1')
        directory = entry.get('directory', '')
        if not re.fullmatch(r'[0-9]+', directory) or int(directory) != ordinal:
            raise ValueError('Invalid inventory directory')
        for key, value in [('urls', url_key(entry['url'])), ('directories', directory)]:
            if value in seen[key]:
                raise ValueError('Duplicate inventory ' + key)
            seen[key].add(value)
    return entries


def inventory_spec(course):
    return {k: course.get(k) for k in ('course_id', 'index_url', 'title_prefix', 'order')}


def assert_archive_identity(output, course):
    """Never reuse an archive for another course, even with --refresh."""
    for filename in ('course.json', 'inventory.json', 'manifest.json'):
        path = output / filename
        if not path.exists():
            continue
        previous = json.loads(path.read_text())
        if previous.get('course_id') and previous['course_id'] != course['course_id']:
            raise ValueError('Archive belongs to a different course: ' + filename)
        if previous.get('index_url') and url_key(previous['index_url']) != url_key(course['index_url']):
            raise ValueError('Archive index_url differs: ' + filename)
        if not previous.get('course_id') and course['course_id'] != 'civilization':
            raise ValueError('Legacy archive requires an explicit identity migration')
        if filename == 'course.json':
            for kind, binding in previous.get('destinations', {}).items():
                if course.get('destinations', {}).get(kind) != binding:
                    raise ValueError('Destination change requires an explicit migration; edit the private archived course.json after reconciliation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profiles', nargs='+', type=Path)
    parser.add_argument('--destinations', choices=('notion', 'obsidian', 'both'))
    args = parser.parse_args()
    try:
        courses = [load_course(p, args.destinations) for p in args.profiles]
        check_isolation(courses)
        print(json.dumps({'ok': True, 'courses': [c['course_id'] for c in courses]}))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
