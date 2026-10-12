"""Whole-course audits must use the selected inventory and destination."""
import json
from pathlib import Path
import tempfile
import unittest

from audit_course import audit_course
from extract_sources import extract


PARENT = '22222222-2222-2222-2222-222222222222'


class CourseAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.course = {'schema_version': 1, 'course_id': 'sample', 'title': 'Sample', 'title_prefix': 'Sample',
                       'index_url': 'https://example.test/tag/sample/',
                       'destinations': {'notion': {'root_id': '33333333-3333-3333-3333-333333333333', 'lecture_parent_id': PARENT}}}
        self.write(self.root / 'course.json', self.course)
        entries = []
        for n in (1, 2):
            url = f'https://example.test/sample-{n}/'
            entry = {'course_id': 'sample', 'lecture_number': n, 'title': f'Sample #{n}: Test',
                     'source_label': f'#{n}', 'directory': f'{n:02d}', 'url': url}
            entries.append(entry)
            folder = self.root / entry['directory']; folder.mkdir()
            source = extract(f'<html><body><h1>{entry["title"]}</h1><div class="gh-content"><p>' + 'Synthetic. ' * 501 + '</p></div></body></html>', url, entry, {})
            title = f'{n:02d} · Test'
            page_id = f'11111111-1111-1111-1111-{n:012d}'
            neighbor = f'11111111-1111-1111-1111-{3-n:012d}'
            content = f'Original exercise. [Source]({url}) [Neighbor](https://app.notion.com/p/{neighbor})'
            props = {'Name': title, 'Lecture': n, 'Kind': 'Lecture', 'Topics': ['Test'], 'Reading': 'To read', 'Source': url,
                     'Source words': source['counts']['words'], 'Figures': 0, 'QA': 'Reviewed'}
            notes = {'schema_version': 1, 'course_id': 'sample', 'source_label': entry['source_label'], 'lecture_number': n,
                     'title': title, 'source_url': url, 'source_sha256': source['hashes']['article_text_sha256'],
                     'properties': props, 'content': content, 'figures': [],
                     'coverage': {'read_source_ids': [b['id'] for b in source['blocks']]},
                     'audit': {'full_source_read': True, 'semantic_reviewed': True, 'draft_ready': True,
                               'source_derived_words': 0, 'quoted_words': 0, 'rights_basis': 'protected-web-default', 'limitations': []},
                     'publication': {'page_id': page_id, 'parent_id': PARENT},
                     'navigation': {'next' if n == 1 else 'previous': neighbor}}
            raw = {'text': f'<page url="https://app.notion.com/p/{page_id}">\n<parent-data-source url="collection://{PARENT}"/>\n<properties>\n{json.dumps(props)}\n</properties>\n<content>\n{content}\n</content>\n</page>'}
            for filename, value in [('source.json', source), ('notes.json', notes), ('notion-readback.json', raw)]:
                self.write(folder / filename, value)
        self.inventory = {'course_id': 'sample', 'lecture_count': 2, 'advertised_lecture_count': 2, 'lectures': entries,
                          'integrity': {'pagination_terminated': True}}
        self.write(self.root / 'inventory.json', self.inventory)

    def write(self, path, value):
        path.write_text(json.dumps(value))

    def tearDown(self):
        self.tmp.cleanup()

    def test_two_item_course_audits_and_navigation_stops_at_actual_end(self):
        result = audit_course(self.root, published=True, navigation=True)
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual(result['counts']['lectures'], 2)
        self.assertEqual(result['expected_count'], 2)

    def test_missing_item_cannot_pass_partial_course_as_complete(self):
        (self.root / '02' / 'notes.json').unlink()
        self.assertFalse(audit_course(self.root)['ok'])

    def test_wrong_course_destination_is_rejected(self):
        self.course['destinations']['notion']['lecture_parent_id'] = '44444444-4444-4444-4444-444444444444'
        self.write(self.root / 'course.json', self.course)
        result = audit_course(self.root, published=True)
        self.assertTrue(any('outside this course destination' in e for e in result['errors']))

    def test_inventory_url_mismatch_cannot_pass(self):
        self.inventory['lectures'][1]['url'] = 'https://example.test/other/'
        self.write(self.root / 'inventory.json', self.inventory)
        self.assertFalse(audit_course(self.root)['ok'])

    def test_distinct_requested_urls_cannot_share_canonical_identity(self):
        path = self.root / '02' / 'source.json'
        source = json.loads(path.read_text())
        source['canonical_url'] = 'https://example.test/sample-1/'
        self.write(path, source)
        result = audit_course(self.root)
        self.assertTrue(any('Duplicate canonical source' in e for e in result['errors']))

    def test_dashed_and_compact_notion_ids_are_one_page(self):
        path = self.root / '02' / 'notes.json'
        notes = json.loads(path.read_text())
        old_id = notes['publication']['page_id']
        notes['publication']['page_id'] = '11111111111111111111000000000001'
        self.write(path, notes)
        raw_path = self.root / '02' / 'notion-readback.json'
        raw_path.write_text(raw_path.read_text().replace(old_id, notes['publication']['page_id']))
        result = audit_course(self.root, published=True)
        self.assertTrue(any('duplicate published page' in e for e in result['errors']))

    def test_failed_refresh_cannot_be_hidden_by_preexisting_valid_notes(self):
        manifest = {'course_id': 'sample', 'expected_count': 2, 'archived_count': 1,
                    'lectures': self.inventory['lectures'][:1],
                    'failures': [{'lecture_number': 2, 'error': 'Synthetic timeout'}]}
        self.write(self.root / 'manifest.json', manifest)
        result = audit_course(self.root)
        self.assertTrue(any('unresolved failures' in e for e in result['errors']))
        self.assertTrue(any('incomplete' in e for e in result['errors']))


if __name__ == '__main__':
    unittest.main()
