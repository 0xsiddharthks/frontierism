import tempfile
import unittest
from pathlib import Path

from export_obsidian import convert, markdown_table, validate_wikilinks


class ObsidianExportTests(unittest.TestCase):
    def test_nested_details_and_table_stay_inside_callouts(self):
        source = '<details>\n<summary>Concept</summary>\n\tBefore\n\t<details>\n\t<summary>Answer cues</summary>\n\t\tA\n\t</details>\n\t<table><tr><td>Choice</td><td>Value</td></tr><tr><td>A</td><td>4</td></tr></table>\n</details>'
        result = convert(source, pages={}, images={}, files={})
        self.assertIn('> > [!question]- Answer cues', result)
        self.assertIn('> | Choice | Value |', result)
        self.assertIn('> | A | 4 |', result)
        self.assertIn('>\n> | Choice | Value |', result)
        self.assertNotIn('<details>', result)

    def test_native_links_images_and_attachment(self):
        source = '<mention-page url="https://app.notion.com/p/abc"/>\n![Map](https://example.com/a.webp)\n<file src="notion-file-block://a?x=1&amp;y=2"></file>'
        result = convert(source, pages={'abc': 'course/02'}, images={'https://example.com/a.webp': 'course/assets/a.webp'}, files={'notion-file-block://a?x=1&y=2': 'course/source#Record'})
        self.assertEqual(result.count('![[course/assets/a.webp]]'), 1)
        self.assertIn('[[course/02|02]]', result)
        self.assertIn('![[course/source#Record]]', result)
        self.assertNotIn('https://example.com', result)

    def test_missing_asset_fails_instead_of_silently_linking(self):
        with self.assertRaisesRegex(ValueError, 'not been archived'):
            convert('![Map](https://example.com/a.webp)', pages={}, images={}, files={})

    def test_unknown_blocks_require_review(self):
        with self.assertRaisesRegex(ValueError, 'Unconverted'):
            convert('<database url="x"/>', pages={}, images={}, files={})

    def test_columns_keep_captions_with_their_images(self):
        source = '<columns><column ratio="50">![A](a)</column><column ratio="50">![B](b)</column></columns>'
        result = convert(source, pages={}, images={'a': 'a.webp', 'b': 'b.webp'}, files={})
        self.assertIn('> [!gallery]', result)
        self.assertEqual(result.count('> > [!figure]'), 2)
        self.assertIn('> > *A*', result)

    def test_table_does_not_silently_flatten_spans(self):
        with self.assertRaisesRegex(ValueError, 'Spanning'):
            markdown_table('<table><tr><td colspan="2">A</td></tr></table>')

    def test_link_audit_detects_missing_and_ambiguous_targets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'a').mkdir(); (root / 'b').mkdir()
            (root / 'a/note.md').write_text('')
            (root / 'b/note.md').write_text('')
            (root / 'index.md').write_text('[[a/note]] [[note]] ![[missing.webp]] [[a/note#Absent]]')
            errors = validate_wikilinks(root)
            self.assertEqual({e['target'] for e in errors}, {'note', 'missing.webp', 'a/note#Absent'})


if __name__ == '__main__':
    unittest.main()
