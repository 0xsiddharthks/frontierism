import tempfile
import unittest
from pathlib import Path

from export_obsidian import convert, markdown_table, notion_page_id, space_blocks, validate_wikilinks


class ObsidianExportTests(unittest.TestCase):
    def test_adjacent_answers_become_independent_foldable_callouts(self):
        source = '\n'.join(f'<details>\n<summary>{n}. Question?</summary>\n\tAnswer {n}.\n</details>' for n in range(1, 5))
        result = convert(source, pages={}, images={}, files={})
        self.assertEqual(result, '\n\n'.join(f'> [!question]- {n}. Question?\n> Answer {n}.' for n in range(1, 5)) + '\n')

    def test_nested_sibling_callouts_keep_their_parent(self):
        source = '> [!info] Parent\n> > [!question]- First\n> > One\n> > [!question]- Second\n> > Two'
        self.assertEqual(space_blocks(source), '> [!info] Parent\n> > [!question]- First\n> > One\n>\n> > [!question]- Second\n> > Two')

    def test_callout_examples_inside_quoted_code_stay_literal(self):
        source = '> [!info] Example\n> ```markdown\n> [!question]- First\n> One\n> [!question]- Second\n> Two\n> ```'
        self.assertEqual(space_blocks(source), source)

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

    def test_soft_wrapped_prose_and_list_indentation_are_preserved(self):
        source = 'One paragraph\ncontinues here.\n\n- Parent\n\t- Child\n\t  continuation\n- Next'
        self.assertEqual(convert(source, pages={}, images={}, files={}), source + '\n')

    def test_code_examples_are_not_converted_or_compacted(self):
        source = ('````markdown\n```\n![Example](not-archived)\n\n\n'
                  '<mention-page url="https://app.notion.com/p/unknown"/>\n'
                  '<details><summary>Literal</summary>Text</details>\n````')
        self.assertEqual(convert(source, pages={}, images={}, files={}), source + '\n')

    def test_tilde_code_fences_are_literal(self):
        source = '~~~markdown\n<unknown/>\n![Image](missing)\n~~~'
        self.assertEqual(convert(source, pages={}, images={}, files={}), source + '\n')

    def test_inline_code_and_escaped_examples_are_literal(self):
        source = ('Use `![x](missing)` and `` `<unknown/>` ``.\n'
                  r'Write \<unknown/> or \![x](missing) or \[[sample]].')
        self.assertEqual(convert(source, pages={}, images={}, files={}), source + '\n')

    def test_fenced_code_inside_details_retains_every_quoted_line(self):
        source = '<details>\n<summary>Code</summary>\n\t```python\n\tif ok:\n\t    run()\n\t\n\t```\n</details>'
        result = convert(source, pages={}, images={}, files={})
        self.assertIn('> ```python\n> if ok:\n>     run()\n> \n> ```', result)

    def test_nested_lists_inside_details_keep_relative_indentation(self):
        source = '<details>\n<summary>Plan</summary>\n\t- Parent\n\t\t- Child\n\t\t  More\n</details>'
        result = convert(source, pages={}, images={}, files={})
        self.assertIn('> - Parent\n> \t- Child\n> \t  More', result)

    def test_custom_attachment_labels_keep_the_caption_and_embed_once(self):
        result = convert('<file src="notion-file-block://report">Annual report, revised.</file>',
                         pages={}, images={}, files={'notion-file-block://report': 'assets/report.pdf'},
                         file_labels={'notion-file-block://report': 'Annual report'}, attachment_label='Attachment')
        self.assertIn('> [!info]- Annual report', result)
        self.assertIn('Annual report, revised.', result)
        self.assertEqual(result.count('![[assets/report.pdf]]'), 1)
        self.assertNotIn('Source record', result)

    def test_image_without_caption_does_not_gain_empty_emphasis(self):
        self.assertEqual(convert('![](image)', pages={}, images={'image': 'assets/image.png'}, files={}),
                         '![[assets/image.png]]\n')

    def test_normalize_notion_url_shapes(self):
        compact = '0123456789abcdef0123456789abcdef'
        hyphenated = '01234567-89ab-cdef-0123-456789abcdef'
        for value in (compact, hyphenated.upper(), 'https://app.notion.com/p/' + hyphenated + '?source=copy_link',
                      'https://www.notion.so/workspace/Some-title-' + compact + '?v=view',
                      'https://workspace.notion.site/Some-title-' + compact,
                      'https://www.notion.so/?p=' + compact):
            with self.subTest(value=value):
                self.assertEqual(notion_page_id(value), compact)

    def test_markdown_notion_links_preserve_aliases(self):
        identifier = '0123456789abcdef0123456789abcdef'
        result = convert('[incentives](https://www.notion.so/Readable-title-' + identifier + '?source=copy_link)',
                         pages={identifier: 'notes/Decision'}, images={}, files={})
        self.assertEqual(result, '[[notes/Decision|incentives]]\n')

    def test_verified_external_page_stays_a_web_link(self):
        identifier = '0123456789abcdef0123456789abcdef'
        url = 'https://www.notion.so/' + identifier
        result = convert('[Background](' + url + '?source=copy_link)\n<mention-page url="' + url + '"/>',
                         pages={}, images={}, files={}, external_pages={identifier: url})
        self.assertIn('[Background](' + url + ')', result)
        self.assertIn('[Notion page](' + url + ')', result)
        self.assertNotIn('[[', result)

    def test_unmapped_page_and_mismatched_external_identity_fail(self):
        with self.assertRaisesRegex(ValueError, 'Unmapped'):
            convert('[Missing](https://www.notion.so/abc)', pages={}, images={}, files={})
        with self.assertRaisesRegex(ValueError, 'does not match'):
            convert('Text', pages={}, images={}, files={}, external_pages={'abc': 'https://www.notion.so/def'})

    def test_block_anchor_is_never_silently_discarded(self):
        source = '[Section](https://www.notion.so/abc#block)'
        with self.assertRaisesRegex(ValueError, 'block anchor'):
            convert(source, pages={'abc': 'note'}, images={}, files={})
        result = convert(source, pages={'abc': 'note'}, images={}, files={}, external_pages={'abc': 'https://www.notion.so/abc'})
        self.assertEqual(result, source + '\n')

    def test_unsafe_generated_paths_fail(self):
        for target in ('../../private', '/tmp/note', 'C:/note', 'note|alias', 'note\nextra'):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'Unsafe'):
                convert('![Map](image)', pages={}, images={'image': target}, files={})

    def test_table_wrappers_and_line_breaks_preserve_cells(self):
        table = '<table><thead><tr><th>A</th><th>B</th></tr></thead><tbody><tr><td>one<br>two</td><td>x|y</td></tr></tbody></table>'
        self.assertIn('| one<br>two | x\\|y |', markdown_table(table))

    def test_malformed_table_fails(self):
        with self.assertRaises(ValueError):
            markdown_table('<table><tr><td>Open</table>')

    def test_native_link_audit_skips_code_and_escaped_examples(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'note.md').write_text('`[[inline]]`\n\\[[escaped]]\n\n~~~markdown\n[[fenced]]\n~~~\n\n> ```\n> [[quoted]]\n> ```\n')
            self.assertEqual(validate_wikilinks(root), [])

    def test_same_note_and_relative_fragments_resolve(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'nested').mkdir()
            (root / 'index.md').write_text('# Main heading\n\nA paragraph ^anchor\n')
            (root / 'nested/note.md').write_text('# Local\n[[#Local]] [[../index#Main%20heading]] [[../index#^anchor]]\n')
            self.assertEqual(validate_wikilinks(root), [])

    def test_link_audit_rejects_escaping_paths_and_external_symlinks(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as outside:
            root = Path(folder)
            external = Path(outside) / 'secret.md'
            external.write_text('# Secret\n')
            (root / 'alias.md').symlink_to(external)
            (root / 'index.md').write_text('[[../escape]] [[alias]]')
            errors = validate_wikilinks(root)
            self.assertEqual({item['target'] for item in errors}, {'../escape', 'alias'})
            self.assertTrue(all(item['error'] == 'unsafe path' for item in errors))

    def test_heading_inside_code_is_not_a_real_fragment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'note.md').write_text('```markdown\n# Fake\n```\n[[#Fake]]')
            self.assertEqual(validate_wikilinks(root)[0]['error'], 'missing fragment')

    def test_inline_code_pipe_does_not_split_a_table_cell(self):
        result = convert('<table><tr><td>Code</td></tr><tr><td>`a|b`</td></tr></table>', pages={}, images={}, files={})
        self.assertIn('| `a\\|b` |', result)

    def test_aliased_wikilinks_inside_markdown_tables_resolve(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'target.md').write_text('Content\n')
            (root / 'index.md').write_text('| Page |\n| --- |\n| [[target\\|Alias]] |\n')
            self.assertEqual(validate_wikilinks(root), [])

    def test_unknown_notion_link_with_hover_title_fails(self):
        with self.assertRaisesRegex(ValueError, 'hover titles'):
            convert('[Title](https://www.notion.so/unknown "hover")', pages={}, images={}, files={})

    def test_notion_link_with_angle_wrapped_url_converts(self):
        result = convert('[Title](<https://www.notion.so/abc>)', pages={'abc': 'note'}, images={}, files={})
        self.assertEqual(result, '[[note|Title]]\n')

    def test_nested_callouts_do_not_capture_following_parent_text(self):
        source = '<callout>\n\tBefore\n\t<callout>\n\t\tNested\n\t</callout>\n\tAfter\n</callout>'
        result = convert(source, pages={}, images={}, files={})
        self.assertIn('> > Nested\n>\n> After', result)
        self.assertNotIn('> > After', result)


if __name__ == '__main__':
    unittest.main()
