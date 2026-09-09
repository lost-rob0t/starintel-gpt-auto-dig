from __future__ import annotations

import json
import unittest
from pathlib import Path

import starintel_doc
from conformance.fixtures import all_fixtures
from starintel_doc.spec import TYPE_FIELDS

ROOT = Path(__file__).resolve().parents[1]


class OperationRegistryTests(unittest.TestCase):
    def test_operation_is_registered_for_runtime_and_shared_fixtures(self) -> None:
        self.assertIn("operation", TYPE_FIELDS)
        fixture_types = {
            item["object_type"]
            for item in all_fixtures()
            if item.get("expected_valid")
        }
        self.assertIn("operation", fixture_types)
        self.assertTrue(set(TYPE_FIELDS).issubset(fixture_types))

    def test_release_profile_matches_runtime_inventory(self) -> None:
        expansion = json.loads(
            (ROOT / "schemas" / "starintel-doc-v0.9.0.expansion.json").read_text()
        )
        manifest = json.loads(
            (ROOT / "schemas" / "starintel-doc-v0.9.0.manifest.json").read_text()
        )
        self.assertEqual(set(expansion["dtype_fields"]), set(TYPE_FIELDS))
        self.assertEqual(manifest["dtype_count"], len(TYPE_FIELDS))
        self.assertEqual(manifest["release_version"], "0.9.1")
        self.assertEqual(manifest["profile_version"], "0.9.1")


if __name__ == "__main__":
    unittest.main()
