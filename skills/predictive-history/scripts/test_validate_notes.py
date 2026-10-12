"""Reject plausible but incomplete or misidentified lecture drafts."""
import copy
from pathlib import Path
import tempfile
import unittest

from extract_sources import extract
from validate_notes import validate


class DraftValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / 'source.json'
        html = ('<!doctype html><html><head><link rel="canonical" href="https://example.test/lecture/">'
                '</head><body><h1>Civilization #1: Test</h1><div class="gh-content gh-canvas">'
                '<h2 id="argument">Argument</h2><p>A short source.</p><img src="figure.png">'
                '</div></body></html>')
        self.source = extract(html, 'https://example.test/lecture/',
                              {'lecture_number': 1, 'source_label': '#1', 'title': 'Civilization #1: Test'}, {})
        self.notes = {
            'schema_version': 1, 'lecture_number': 1, 'title': '01 · Test',
            'source_url': 'https://example.test/lecture/',
            'source_sha256': self.source['hashes']['article_text_sha256'],
            'properties': {'Name': '01 · Test', 'Lecture': 1, 'Kind': 'Lecture',
                'Topics': ['History'], 'Era and region': 'Example', 'Reading': 'To read',
                'Source': 'https://example.test/lecture/', 'Source words': self.source['counts']['words'],
                'Figures': 1, 'QA': 'Source checked'},
            'content': '[Source](https://example.test/lecture/)\n\n![Figure](https://example.test/lecture/figure.png)',
            'coverage': {'read_source_ids': [b['id'] for b in self.source['blocks']]},
            'figures': [{'source_id': self.source['figures'][0]['id'], 'status': 'inspected',
                         'disposition': 'embedded', 'note': 'Inspected fixture.'}],
            'audit': {'full_source_read': True, 'semantic_reviewed': True, 'draft_ready': True,
                      'source_derived_words': 10, 'quoted_words': 0,
                      'rights_basis': 'protected-web-default',
                      'source_warnings_reviewed': ['short_article_under_500_words'],
                      'limitations': ['Deliberately short synthetic regression fixture.']}}

    def tearDown(self):
        self.temporary.cleanup()

    def result(self, notes=None):
        return validate(self.source, notes or self.notes, self.path)

    def test_valid_minimal_draft(self):
        self.assertTrue(self.result()['ok'])

    def test_generic_course_identity_and_subject_properties(self):
        self.source.update(course_id='game-theory')
        self.notes.update(course_id='game-theory', source_label='#1')
        self.notes['properties'].pop('Era and region')
        self.notes['properties']['Kind'] = 'Exam'
        self.assertTrue(self.result()['ok'])
        self.notes['course_id'] = 'civilization'
        self.assertFalse(self.result()['ok'])

    def test_end_label_is_preserved_at_any_course_length(self):
        self.source.update(lecture_number=12, source_label='END')
        self.notes['lecture_number'] = 12
        self.notes['properties']['Lecture'] = 12
        self.assertFalse(self.result()['ok'])
        self.notes['title'] = self.notes['properties']['Name'] = '12 · END — Test'
        self.assertTrue(self.result()['ok'])

    def test_link_alone_cannot_claim_an_embed(self):
        notes = copy.deepcopy(self.notes)
        notes['content'] = notes['content'].replace('![Figure]', '[Figure]')
        result = self.result(notes)
        self.assertFalse(result['ok'])
        self.assertTrue(any('native image block' in e for e in result['errors']))

    def test_coverage_and_identity_must_match(self):
        for mutation in ['coverage', 'hash', 'number', 'count']:
            notes = copy.deepcopy(self.notes)
            if mutation == 'coverage':
                notes['coverage']['read_source_ids'].pop()
            elif mutation == 'hash':
                notes['source_sha256'] = '0' * 64
            elif mutation == 'number':
                notes['properties']['Lecture'] = 2
            else:
                notes['properties']['Figures'] = 0
            with self.subTest(mutation=mutation):
                self.assertFalse(self.result(notes)['ok'])

    def test_rights_allowance_cannot_be_silently_raised(self):
        notes = copy.deepcopy(self.notes)
        notes['audit'].update(source_derived_words=250, source_word_limit=300)
        self.assertFalse(self.result(notes)['ok'])

    def test_publication_needs_actual_complete_readback(self):
        result = validate(self.source, self.notes, self.path, require_published=True)
        self.assertFalse(result['ok'])
        self.assertIn('a complete readback record is required', result['errors'])


if __name__ == '__main__':
    unittest.main()
