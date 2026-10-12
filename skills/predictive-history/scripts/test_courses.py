"""Course-size independence, explicit ordering, and destination isolation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from course_config import check_isolation, validate_course
import extract_sources as extractor


def profile(slug='game-theory', prefix='Game Theory'):
    return {'schema_version': 1, 'course_id': slug, 'title': prefix,
            'title_prefix': prefix, 'index_url': 'https://example.test/tag/' + slug + '/'}


def listing(prefix, labels, advertised=None, next_url=None):
    cards = ''.join('<a class="gh-card-link" href="/item-' + str(i) + '/"><h3 class="gh-card-title">' +
                    prefix + ' ' + str(label) + ': Synthetic title</h3></a>' for i, label in enumerate(labels))
    return (f'<p>A collection of {advertised if advertised is not None else len(labels)} issues</p>' + cards +
            (f'<link rel="next" href="{next_url}">' if next_url else '')).encode()


class CourseTests(unittest.TestCase):
    def inventory(self, course, body, folder, refresh=False):
        with patch.object(extractor, 'request', return_value=(body, {'sha256': extractor.digest(body)})):
            return extractor.inventory(course['index_url'], Path(folder), refresh, course=course)

    def test_variable_lengths_and_end_without_hash(self):
        for course, labels in [(profile(), ['#3', '#1', '#2']),
                               (profile('geo-strategy', 'Geo-Strategy'), ['END', '#2', '#1']),
                               (profile('long-course', 'Long Course'), [f'#{n}' for n in range(75, 0, -1)])]:
            with self.subTest(course=course['course_id']), tempfile.TemporaryDirectory() as tmp:
                result = self.inventory(course, listing(course['title_prefix'], labels), tmp)
                self.assertEqual(result['lecture_count'], len(labels))
                self.assertEqual(result['lectures'][0]['source_label'], '#1')
                self.assertEqual(result['lectures'][-1]['source_label'], 'END' if 'END' in labels else '#' + str(len(labels)))
                self.assertEqual(result['course_id'], course['course_id'])

    def test_gaps_duplicate_labels_and_advertised_mismatch_fail(self):
        for labels, advertised in [(['#1', '#3'], 2), (['#1', '#1'], 2), (['#1'], 2)]:
            with self.subTest(labels=labels), tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
                self.inventory(profile(), listing('Game Theory', labels, advertised), tmp)

    def test_number_can_touch_series_name_as_on_geo_strategy_archive(self):
        course = profile('geo-strategy', 'Geo-Strategy')
        body = listing('Geo-Strategy', ['#1', '#2', 'END']).replace(b'Geo-Strategy #2:', b'Geo-Strategy#2:')
        with tempfile.TemporaryDirectory() as tmp:
            result = self.inventory(course, body, tmp)
            self.assertEqual(result['lectures'][1]['source_label'], '#2')
            self.assertEqual(result['lectures'][2]['source_label'], 'END')

    def test_explicit_order_retains_unnumbered_and_variant_items(self):
        course = profile('meetups', 'Global Meet-Up')
        course['order'] = ['https://example.test/item-2/', 'https://example.test/item-0/', 'https://example.test/item-1/']
        body = listing('Global Meet-Up', ['Special Q&A', '#1A', '#1A'])
        with tempfile.TemporaryDirectory() as tmp:
            result = self.inventory(course, body, tmp)
            self.assertEqual([x['url'] for x in result['lectures']], course['order'])
            self.assertEqual([x['source_label'] for x in result['lectures']], ['#1A', None, '#1A'])
        course['order'].pop()
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, 'every discovered'):
            self.inventory(course, body, tmp)

    def test_real_pagination_and_repeat_card_are_deduplicated(self):
        course = profile()
        page1 = listing('Game Theory', ['#1'], 2, '/tag/game-theory/page/2/')
        page2 = listing('Game Theory', ['#1', '#2'], 2)
        responses = [(b, {'sha256': extractor.digest(b)}) for b in (page1, page2)]
        with tempfile.TemporaryDirectory() as tmp, patch.object(extractor, 'request', side_effect=responses) as request:
            result = extractor.inventory(course['index_url'], Path(tmp), course=course)
            self.assertEqual(result['lecture_count'], 2)
            self.assertEqual(request.call_args_list[1].args[0], 'https://example.test/tag/game-theory/page/2/')

    def test_pagination_cycle_fails(self):
        course = profile()
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, 'cycle'):
            self.inventory(course, listing('Game Theory', ['#1'], 1, course['index_url']), tmp)

    def test_archive_cannot_be_reused_for_another_course_even_on_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.inventory(profile(), listing('Game Theory', ['#1']), tmp)
            for refresh in (False, True):
                with self.subTest(refresh=refresh), self.assertRaisesRegex(ValueError, 'different course'):
                    self.inventory(profile('secret-history', 'Secret History'), listing('Secret History', ['#1']), tmp, refresh)

    def test_refresh_adds_episodes_without_renumbering_existing_sources(self):
        course = profile()
        with tempfile.TemporaryDirectory() as tmp:
            self.inventory(course, listing('Game Theory', ['#1']), tmp)
            result = self.inventory(course, listing('Game Theory', ['#1', '#2']), tmp, True)
            self.assertEqual(result['lectures'][0]['url'], 'https://example.test/item-0/')
            self.assertEqual(result['lecture_count'], 2)
            with self.assertRaisesRegex(ValueError, 'renumber'):
                self.inventory(course, listing('Game Theory', ['#2', '#1']), tmp, True)

    def test_cached_inventory_configuration_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            course = profile()
            self.inventory(course, listing('Game Theory', ['#1']), tmp)
            course['title_prefix'] = 'Different title'
            with self.assertRaisesRegex(ValueError, 'configuration changed'):
                self.inventory(course, b'', tmp)

    def test_separate_roots_and_sibling_folders_pass(self):
        courses = self.destinations()
        check_isolation(courses)
        for course in courses:
            validate_course(course, 'both')

    def destinations(self):
        courses = [profile(), profile('secret-history', 'Secret History')]
        for n, course in enumerate(courses):
            course['destinations'] = {'notion': {'root_id': str(n) * 32, 'lecture_parent_id': str(n + 2) * 32, 'font': 'mono'},
                                      'obsidian': {'vault': '/tmp/synthetic-vault', 'folder': course['course_id']}}
        return courses

    def test_shared_roots_parents_and_overlapping_folders_are_rejected(self):
        for kind in ('root_id', 'lecture_parent_id', 'same-folder', 'nested-folder'):
            courses = self.destinations()
            if kind in ('root_id', 'lecture_parent_id'):
                courses[1]['destinations']['notion'][kind] = courses[0]['destinations']['notion'][kind]
            else:
                courses[1]['destinations']['obsidian']['folder'] = 'game-theory' + ('/nested' if kind == 'nested-folder' else '')
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                check_isolation(courses)

    def test_unsafe_vault_folder_is_rejected(self):
        for folder in ('', '.', '../civilization', '/tmp/other'):
            course = self.destinations()[0]
            course['destinations']['obsidian']['folder'] = folder
            with self.subTest(folder=folder), self.assertRaises(ValueError):
                validate_course(course)

    def test_placeholder_notion_destination_is_not_ready_for_publication(self):
        course = self.destinations()[0]
        course['destinations']['notion']['root_id'] = 'actual-course-root-id'
        with self.assertRaisesRegex(ValueError, 'actual UUIDs'):
            validate_course(course, 'notion')

    def test_partial_extraction_retains_the_complete_expected_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'archive'
            config = Path(tmp) / 'course.json'
            config.write_text(json.dumps(profile()))
            body = listing('Game Theory', ['#1', '#2'])
            args = ['extract_sources.py', '--course', str(config), '--output', str(output), '--lecture', '2']
            def archived(item, *args):
                return {**item, 'counts': {'words': 10, 'figures': 0, 'tables': 0}, 'warnings': []}
            with patch('sys.argv', args), patch.object(extractor, 'request', return_value=(body, {})), patch.object(extractor, 'archive_lecture', side_effect=archived):
                self.assertEqual(extractor.main(), 0)
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(manifest['expected_count'], 2)
            self.assertEqual(manifest['archived_count'], 1)
            self.assertEqual(manifest['lectures'][0]['lecture_number'], 2)


if __name__ == '__main__':
    unittest.main()
