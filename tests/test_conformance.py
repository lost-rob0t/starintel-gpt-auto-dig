from __future__ import annotations

import unittest

from conformance.adapter import error_category, handle
from conformance.fixtures import all_fixtures
from starintel_doc.spec import SCHEMA_VERSION, TYPE_FIELDS
from starintel_doc.validation import ValidationError


class ConformanceFixtureTests(unittest.TestCase):
    def test_every_registered_dtype_has_a_minimal_fixture(self) -> None:
        covered = {
            value["object_type"]
            for value in all_fixtures()
            if value["expected_valid"] and value["fixture_id"].endswith(".minimal.v1")
        }
        self.assertEqual(set(TYPE_FIELDS), covered)

    def test_fixture_ids_are_unique(self) -> None:
        identifiers = [value["fixture_id"] for value in all_fixtures()]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_valid_fixtures_roundtrip_without_mutation(self) -> None:
        for value in all_fixtures():
            if not value["expected_valid"]:
                continue
            with self.subTest(value["fixture_id"]):
                response = handle(
                    {
                        "command": "roundtrip",
                        "spec_version": SCHEMA_VERSION,
                        "document": value["document"],
                    }
                )
                self.assertTrue(response["ok"])
                self.assertEqual(value["document"], response["document"])

    def test_invalid_fixtures_have_stable_categories(self) -> None:
        for value in all_fixtures():
            if value["expected_valid"]:
                continue
            with self.subTest(value["fixture_id"]):
                try:
                    handle(
                        {
                            "command": "validate",
                            "spec_version": SCHEMA_VERSION,
                            "document": value["document"],
                        }
                    )
                except ValidationError as exc:
                    self.assertEqual(value["expected_error"], error_category(str(exc)))
                else:
                    self.fail("invalid fixture was accepted")


if __name__ == "__main__":
    unittest.main()
