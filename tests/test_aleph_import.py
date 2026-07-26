from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "import_aleph_public.py"
SPEC = importlib.util.spec_from_file_location("import_aleph_public", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AlephImportTests(unittest.TestCase):
    def test_api_key_header_is_normalized(self) -> None:
        self.assertEqual("", MODULE.authorization_value(""))
        self.assertEqual("ApiKey secret", MODULE.authorization_value("secret"))
        self.assertEqual("ApiKey secret", MODULE.authorization_value("ApiKey secret"))

    def test_followthemoney_company_maps_to_valid_org(self) -> None:
        document = MODULE.entity_document(
            {
                "id": "company-1",
                "schema": "Company",
                "name": "Example Company",
                "collection_id": "public-records",
                "properties": {
                    "name": ["Example Company"],
                    "jurisdiction": ["Ohio"],
                    "registrationNumber": ["12345"],
                },
            },
            "https://aleph.occrp.org",
        )
        self.assertIsNotNone(document)
        assert document is not None
        self.assertEqual("org", document["dtype"])
        self.assertEqual("Example Company", document["data"]["name"])
        self.assertEqual("occrp-aleph-public-records", document["dataset"])


if __name__ == "__main__":
    unittest.main()
