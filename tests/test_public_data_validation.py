import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_public_data import validate_news, validate_payload  # noqa: E402


class PublicDataValidationTests(unittest.TestCase):
    def test_private_yahoo_keys_are_rejected(self):
        errors = validate_payload(
            pathlib.Path("fixture.json"),
            {"schema_version": 1, "short_invitation_url": "private"},
        )
        self.assertTrue(errors)

    def test_feed_errors_are_rejected_as_news(self):
        errors = validate_news(
            {
                "schema_version": 1,
                "items": [
                    {
                        "title": "Feed error: unavailable",
                        "link": "https://example.invalid/error",
                    }
                ],
            }
        )
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
