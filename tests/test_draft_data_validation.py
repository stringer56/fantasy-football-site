from __future__ import annotations

import copy
import contextlib
import io
import unittest
from unittest import mock

from scripts import validate_draft_data


class DraftDataValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.datasets = {
            name: validate_draft_data.load(name)
            for name in ("drafts.yml", "franchises.yml", "seasons.yml")
        }

    def test_committed_draft_archive_passes(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            validate_draft_data.main()
        self.assertIn("Validated 4 drafts", output.getvalue())

    def test_duplicate_draft_slot_is_rejected(self) -> None:
        datasets = copy.deepcopy(self.datasets)
        datasets["drafts.yml"]["drafts"][0]["draft_order"][1]["slot"] = 1

        with mock.patch.object(validate_draft_data, "load", side_effect=datasets.__getitem__):
            with self.assertRaisesRegex(SystemExit, "draft slots must be unique"):
                validate_draft_data.main()

    def test_unresolved_mapping_cannot_hide_a_franchise_id(self) -> None:
        datasets = copy.deepcopy(self.datasets)
        unresolved = next(
            entry
            for draft in datasets["drafts.yml"]["drafts"]
            for entry in draft["draft_order"]
            if entry["mapping_status"] == "unresolved"
        )
        unresolved["franchise_id"] = "maine-moose"

        with mock.patch.object(validate_draft_data, "load", side_effect=datasets.__getitem__):
            with self.assertRaisesRegex(SystemExit, "unresolved mapping must have a null franchise_id"):
                validate_draft_data.main()


if __name__ == "__main__":
    unittest.main()
