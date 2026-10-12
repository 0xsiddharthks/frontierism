"""Regression tests for failures that could otherwise falsely certify a page."""
import copy
import unittest

from record_readback import normalize


PAGE = '11111111-1111-1111-1111-111111111111'
PARENT = '22222222-2222-2222-2222-222222222222'


def fixture(body='A complete explanation.\n[Source](https://example.org/article/)'):
    notes = {'lecture_number': 1, 'content': body,
             'publication': {'page_id': PAGE, 'parent_id': PARENT}}
    raw = {'text': '<page url="https://app.notion.com/p/' + PAGE + '">\n'
           '<parent-data-source url="collection://' + PARENT + '"/>\n'
           '<properties>\n{"Lecture":1}\n</properties>\n'
           '<content>\n' + body + '\n</content>\n</page>',
           'truncated': False, 'unknown_block_count': 0}
    return notes, raw


class ReadbackTests(unittest.TestCase):
    def test_complete_body_is_read_from_fetch(self):
        notes, raw = fixture()
        result = normalize(raw, notes)
        self.assertEqual(result['content'], notes['content'])
        self.assertEqual(result['properties'], {'Lecture': 1})

    def test_truncation_in_either_envelope_is_rejected(self):
        notes, raw = fixture()
        for wrapper in [dict(raw, truncated=True),
                        {'structuredContent': raw, 'truncated': True}]:
            with self.subTest(wrapper=wrapper), self.assertRaises(ValueError):
                normalize(wrapper, notes)

    def test_missing_tail_and_unsupported_blocks_are_rejected(self):
        notes, raw = fixture()
        for mutation in [dict(raw, text=raw['text'].replace('</content>', '')),
                         dict(raw, unknown_block_count=1),
                         dict(raw, unknown_block_ids=['unread'])]:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                normalize(mutation, notes)

    def test_text_or_destination_changes_are_not_ignored(self):
        notes, raw = fixture()
        for old, new in [('complete explanation', 'different explanation'),
                         ('example.org', 'different.org'), (PAGE, PARENT)]:
            changed = dict(raw, text=raw['text'].replace(old, new))
            with self.subTest(old=old), self.assertRaises(ValueError):
                normalize(changed, notes)

    def test_punctuation_serialization_has_explicit_equivalence(self):
        notes, raw = fixture('The price is $10.')
        raw['text'] = raw['text'].replace('$10', '\\$10')
        result = normalize(raw, notes)
        self.assertTrue(result['verification']['content_equivalent'])

    def test_recorded_attachment_can_acquire_a_block_uri(self):
        notes, raw = fixture('<file src="file-upload://upload-id"></file>')
        notes['attachments'] = [{'markdown_source': 'file-upload://upload-id',
                                 'filename': 'source-record.json'}]
        raw['text'] = raw['text'].replace('file-upload://upload-id',
            'notion-file-block://block/file?name=source-record.json')
        result = normalize(raw, notes)
        self.assertTrue(result['verification']['content_equivalent'])
        changed = copy.deepcopy(raw)
        changed['text'] = changed['text'].replace('source-record.json', 'wrong.json')
        with self.assertRaises(ValueError):
            normalize(changed, notes)

    def test_unrecorded_attachment_rebinding_fails(self):
        notes, raw = fixture('<file src="file-upload://upload-id"></file>')
        raw['text'] = raw['text'].replace('file-upload://upload-id',
            'notion-file-block://block/file?name=source-record.json')
        with self.assertRaises(ValueError):
            normalize(raw, notes)


if __name__ == '__main__':
    unittest.main()
