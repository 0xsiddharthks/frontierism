import copy
import unittest

from notion_cli_readback import inspect_export


class CompletenessTest(unittest.TestCase):
    identity = "00000000-0000-4000-8000-000000000001"

    def payload(self):
        return {"page": {"id": self.identity, "in_trash": False},
                "markdown": {"id": self.identity, "markdown": "## Summary\nA complete note.",
                             "truncated": False, "unknown_block_ids": []}}

    def test_complete_export_retains_identity_and_counts(self):
        facts = inspect_export(self.payload(), self.identity)
        self.assertEqual(facts["unknown_block_count"], 0)
        self.assertEqual(facts["words"], 5)

    def test_unknown_or_missing_completeness_information_fails(self):
        for change in [{"truncated": True}, {"unknown_block_ids": ["unknown"]},
                       {"truncated": None}, {"unknown_block_ids": None}]:
            payload = self.payload()
            payload["markdown"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                inspect_export(payload, self.identity)

    def test_wrong_identity_or_archived_page_fails(self):
        baseline = self.payload()
        for target, key, value in [("page", "id", "00000000-0000-4000-8000-000000000002"),
                                   ("markdown", "id", "00000000-0000-4000-8000-000000000002"),
                                   ("page", "in_trash", True)]:
            payload = copy.deepcopy(baseline)
            payload[target][key] = value
            with self.subTest(target=target, key=key), self.assertRaises(ValueError):
                inspect_export(payload, self.identity)

    def test_malformed_export_or_identity_fails(self):
        for payload in [None, [], {}, {"page": {"id": None}, "markdown": {}}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                inspect_export(payload, self.identity)


if __name__ == "__main__":
    unittest.main()
