from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "reconcile_global_shapers_identities.py"
SPEC = importlib.util.spec_from_file_location("global_shapers_reconcile", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def person(document_id: str, name: str, url: str) -> dict:
    return {
        "_id": document_id,
        "dtype": "person",
        "data": {"full_name": name},
        "sources": [{"url": url}],
    }


class GlobalShapersIdentityReconciliationTests(unittest.TestCase):
    def test_generic_official_url_is_not_identity_key(self) -> None:
        left = MODULE.identity_from_document(
            person("person:a", "Alice Example", "https://www.globalshapers.org/"),
            "current-api",
        )
        right = MODULE.identity_from_document(
            person("person:b", "Bob Example", "https://www.globalshapers.org/"),
            "legacy-prefix",
        )
        self.assertEqual(left.official_urls, set())
        self.assertEqual(right.official_urls, set())
        report = MODULE.reconcile([left, right])
        self.assertEqual(report["reconciled_unique_people"], 2)
        self.assertEqual(report["duplicates_reconciled"], 0)

    def test_person_specific_global_shapers_url_is_strong_key(self) -> None:
        url = "https://www.globalshapers.org/member-details/alice-example?utm_source=test"
        left = MODULE.identity_from_document(person("person:a", "Alice Example", url), "current-api")
        right = MODULE.identity_from_document(person("person:b", "Alice E. Example", url), "legacy-prefix")
        self.assertEqual(
            left.official_urls,
            {"https://www.globalshapers.org/member-details/alice-example"},
        )
        report = MODULE.reconcile([left, right])
        self.assertEqual(report["reconciled_unique_people"], 1)
        self.assertEqual(report["strong_match_events"]["official"], 1)

    def test_only_personal_linkedin_urls_are_strong_keys(self) -> None:
        company = "https://www.linkedin.com/company/global-shapers-community/"
        personal = "https://www.linkedin.com/in/alice-example/"
        company_identity = MODULE.identity_from_document(
            person("person:company", "Company Shared", company),
            "current-api",
        )
        self.assertEqual(company_identity.linkedin_urls, set())
        self.assertIn(
            "https://linkedin.com/company/global-shapers-community",
            company_identity.social_urls,
        )

        left = MODULE.identity_from_document(person("person:a", "Alice Example", personal), "current-api")
        right = MODULE.identity_from_document(person("person:b", "Alice Example", personal), "legacy-prefix")
        report = MODULE.reconcile([left, right])
        self.assertEqual(report["reconciled_unique_people"], 1)
        self.assertEqual(report["strong_match_events"]["linkedin"], 1)

    def test_high_fanout_profile_url_collision_is_suppressed(self) -> None:
        shared = "https://www.globalshapers.org/member-details/corrupt-shared-profile"
        identities = [
            MODULE.Identity(
                source="current-api",
                document_id=f"person:{index}",
                name=name,
                normalized_name=MODULE.normalize_text(name),
                official_urls={shared},
            )
            for index, name in enumerate(("Alice Example", "Bob Example", "Carol Example"))
        ]
        report = MODULE.reconcile(identities)
        self.assertEqual(report["reconciled_unique_people"], 3)
        self.assertEqual(report["duplicates_reconciled"], 0)
        self.assertEqual(report["suppressed_strong_key_collision_count"], 1)


if __name__ == "__main__":
    unittest.main()
