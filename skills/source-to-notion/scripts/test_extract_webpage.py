import unittest

from extract_webpage import extract


class ExtractionTest(unittest.TestCase):
    def test_scoping_and_footnotes(self):
        html = '<body><p>Other essay</p><article id="essay"><h2>Title</h2><p>Claim <a href="#note">1</a>.</p><p id="note">Essential qualification.</p></article><p>Next essay</p></body>'
        data = extract(html, "https://example.org/text", "essay")
        self.assertEqual([b["text"] for b in data["blocks"]],
                         ["Title", "Claim 1.", "Essential qualification."])
        self.assertEqual(data["blocks"][1]["links"][0]["url"], "https://example.org/text#note")
        self.assertEqual(data["blocks"][2]["source_id"], "note")
        self.assertEqual(data["coverage"]["status"], "not_read")

    def test_hidden_navigation_and_nested_blocks(self):
        html = '<body><main><nav>Menu</nav><script>bad()</script><p>Visible <span hidden>secret</span>text.</p><ul><li><p>Point one</p></li><li>Point two</li></ul><p aria-hidden="true">Duplicate</p></main></body>'
        text = " ".join(b["text"] for b in extract(html, "https://example.org")["blocks"])
        self.assertEqual(text, "Visible text. Point one Point two")

    def test_unwrapped_text_and_entities(self):
        html = '<article id="x">First <em>premise</em>.<div><p>A &amp; B<br>continue.</p></div>Last sentence.</article>'
        blocks = extract(html, "https://example.org", "x")["blocks"]
        self.assertEqual([b["text"] for b in blocks], ["First premise.", "A & B continue.", "Last sentence."])

    def test_missing_or_duplicate_boundary_fails(self):
        for html in ['<main>Other</main>', '<div id="x">One</div><div id="x">Two</div>']:
            with self.assertRaises(ValueError):
                extract(html, "https://example.org", "x")

    def test_unwrapped_links_retain_their_targets(self):
        html = '<article>Read <a href="/source">the original</a>.<p>A claim.</p><a href="#note">A qualification</a></article>'
        blocks = extract(html, "https://example.org/essay")["blocks"]
        self.assertEqual(blocks[0]["links"],
                         [{"text": "the original", "url": "https://example.org/source"}])
        self.assertEqual(blocks[2]["links"][0]["url"], "https://example.org/essay#note")

    def test_images_and_tables_are_not_marked_inspected(self):
        data = extract('<main><p>See figure</p><img src="/a.png" alt="Chart"><table><tr><td>Value</td></tr></table></main>', "https://example.org")
        self.assertEqual(data["images"][0]["url"], "https://example.org/a.png")
        self.assertEqual(data["images"][0]["inspection"], "not_inspected")
        self.assertTrue(any("Images/tables" in w for w in data["warnings"]))


if __name__ == "__main__":
    unittest.main()
