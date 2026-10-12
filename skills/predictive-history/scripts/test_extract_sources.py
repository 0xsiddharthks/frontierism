#!/usr/bin/env python3
"""Offline regression tests for source completeness, structure, and provenance."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import extract_sources as extractor


class ExtractionTests(unittest.TestCase):
    def source(self, body, extra=""):
        return ('<!doctype html><html><head><link rel="canonical" href="https://example.test/lecture/">'
                '<meta property="article:published_time" content="2025-01-01T00:00:00Z">'
                '</head><body><nav>Outside text<img src="logo.png" alt="Site logo"></nav>'
                '<h1>Civilization #1: Test</h1><div class="gh-content gh-canvas">' + body +
                '</div>' + extra + '<footer>Subscription and navigation text</footer></body></html>')

    def extract(self, body, extra=""):
        source = self.source(body, extra)
        return extractor.extract(source, "https://example.test/lecture/",
                                 {"lecture_number":1,"source_label":"#1","title":"Civilization #1: Test"},
                                 {"http_status":200}), source

    def test_exact_article_boundaries_unicode_and_entities(self):
        result, source = self.extract('<p>Göbekli &amp; Tepe.</p><h2 id="second">Second</h2><p>Final sentence.</p>')
        self.assertEqual(result["article_text"], "Göbekli & Tepe.\n\nSecond\n\nFinal sentence.")
        self.assertNotIn("Outside", result["article_text"])
        self.assertTrue(result["integrity"]["block_text_equals_article_text"])
        self.assertTrue(result["integrity"]["article_closing_tag_present"])
        self.assertEqual(result["hashes"]["original_html_sha256"], hashlib.sha256(source.encode()).hexdigest())
        self.assertEqual(result["headings"][0]["source_id"], "second")
        self.assertEqual(result["blocks"][-1]["heading_id"], "heading-001")

    def test_table_structure_and_cell_separator_preserved(self):
        result, _ = self.extract('<p>Before</p><table><tbody><tr><th>A</th><th>B</th></tr>'
                                 '<tr><td><p>one</p><p>two</p></td><td>x | y</td></tr></tbody></table><p>After</p>')
        self.assertEqual(result["tables"][0]["rows"], [["A","B"],["one two","x | y"]])
        self.assertIn("x \\| y", result["blocks"][1]["markdown"])
        self.assertEqual(result["counts"]["tables"], 1)
        self.assertTrue(result["integrity"]["block_text_equals_article_text"])

    def test_figures_keep_caption_context_and_exclude_logo(self):
        result, _ = self.extract('<h2>Context</h2><p>Before image.</p><figure><img src="../map.webp" alt="map" width="800">'
                                 '<figcaption>Caption from source</figcaption></figure><p>After image.</p>')
        self.assertEqual(len(result["figures"]), 1)
        self.assertEqual(result["figures"][0]["url"], "https://example.test/map.webp")
        self.assertEqual(result["figures"][0]["caption"], "Caption from source")
        self.assertEqual(result["figures"][0]["preceding_text"], "Before image.")
        self.assertEqual(result["figures"][0]["following_text"], "After image.")
        self.assertEqual(len(result["outside_article_images"]), 1)
        self.assertEqual(result["outside_article_images"][0]["alt"], "Site logo")

    def test_gallery_has_one_record_per_image(self):
        result, _ = self.extract('<figure><div><img src="a.png"><img src="b.png"></div></figure><figure><img src="c.png"></figure>')
        self.assertEqual([f["id"] for f in result["figures"]], ["figure-001","figure-002","figure-003"])
        self.assertEqual([f["block_id"] for f in result["figures"]], ["figure-001","figure-001","figure-002"])
        self.assertNotIn("figure_count_mismatch", result["integrity"]["warnings"])

    def test_math_and_literal_powers_preserved(self):
        result, _ = self.extract('<p>E = mc<sup>2</sup>, H<sub>2</sub>O and 3 × 4 = 12.</p><math><mi>x</mi><mo>+</mo><mn>1</mn></math>')
        self.assertIn("<sup>2</sup>", result["blocks"][0]["markdown"])
        self.assertIn("<sub>2</sub>", result["blocks"][0]["markdown"])
        self.assertEqual(result["counts"]["math_nodes"], 3)
        self.assertIn("3 × 4 = 12", result["article_text"])

    def test_paywall_marker_is_flagged(self):
        result, _ = self.extract('<p>Excerpt</p><div class="gh-post-upgrade-cta">Subscribe to read</div>')
        self.assertTrue(result["integrity"]["paywall_detected"])
        self.assertIn("paywall_marker_in_article", result["integrity"]["warnings"])

    def test_mismatch_title_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Card/article title mismatch"):
            extractor.extract(self.source("<p>Text</p>"), "https://example.test/lecture/",
                              {"title":"Civilization #2: Different"}, {})

    def test_end_ordinal_requires_exact_complete_inventory(self):
        cards = ''.join(f'<a class="gh-card-link" href="/{label}/"><h3 class="gh-card-title">Civilization #{label}: Test</h3></a>'
                        for label in [*range(1,60),"END"])
        content = ('<p>A collection of 60 issues</p>' + cards).encode()
        with tempfile.TemporaryDirectory() as temporary, patch.object(extractor,"request",return_value=(content,{"sha256":extractor.digest(content)})):
            result = extractor.inventory("https://example.test/tag/",Path(temporary),course={'schema_version':1,'course_id':'civilization','title':'Civilization','title_prefix':'Civilization','index_url':'https://example.test/tag/'})
            self.assertEqual(result["lectures"][-1]["lecture_number"],60)
            self.assertEqual(result["lectures"][-1]["source_label"],"#END")
        incomplete = content.replace(b'Civilization #1: Test',b'Civilization #61: Test')
        with tempfile.TemporaryDirectory() as temporary, patch.object(extractor,"request",return_value=(incomplete,{})):
            with self.assertRaisesRegex(ValueError,"inventory mismatch"):
                extractor.inventory("https://example.test/tag/",Path(temporary),course={'schema_version':1,'course_id':'civilization','title':'Civilization','title_prefix':'Civilization','index_url':'https://example.test/tag/'})


if __name__ == "__main__":
    unittest.main()
