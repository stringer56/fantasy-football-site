import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pull_news import build_news_payload, parse_feed  # noqa: E402


class NewsPipelineTests(unittest.TestCase):
    def test_rss_items_are_normalized(self):
        xml = b"""<rss><channel><item><title>Story</title><link>https://example.invalid/story</link><pubDate>Today</pubDate></item></channel></rss>"""
        items = parse_feed(xml, "Fixture")
        self.assertEqual(items[0]["source"], "Fixture")
        self.assertEqual(items[0]["title"], "Story")
        self.assertEqual(items[0]["published_at"], "Today")

    def test_atom_items_are_normalized(self):
        xml = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom Story</title><link href="https://example.invalid/atom"/><updated>Today</updated></entry></feed>"""
        items = parse_feed(xml, "Atom")
        self.assertEqual(items[0]["link"], "https://example.invalid/atom")

    def test_all_failures_preserve_previous_valid_news(self):
        existing = {
            "schema_version": 1,
            "updated": 100,
            "items": [{
                "source": "Existing",
                "title": "Valid",
                "link": "https://example.invalid/valid",
                "published_at": "Earlier",
            }],
        }
        payload, should_write = build_news_payload(
            [("One", []), ("Two", [])], existing=existing
        )
        self.assertIs(payload, existing)
        self.assertFalse(should_write)

    def test_all_failures_without_valid_history_produce_empty_data(self):
        existing = {
            "items": [{"title": "[Feed error: hidden]", "link": ""}]
        }
        payload, should_write = build_news_payload([], existing=existing)
        self.assertEqual(payload["items"], [])
        self.assertIsNone(payload["updated"])
        self.assertTrue(should_write)


if __name__ == "__main__":
    unittest.main()
