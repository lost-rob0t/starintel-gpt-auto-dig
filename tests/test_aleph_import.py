from __future__ import annotations

import importlib.util
import argparse
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "import_aleph_public.py"
SPEC = importlib.util.spec_from_file_location("import_aleph_public", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AlephImportTests(unittest.TestCase):
    def test_import_db_round_trips_legacy_producer_output(self) -> None:
        # Exercise the producer's actual CLI dispatch without network access or
        # touching the repository database. Canonical-default dispatch rejects
        # this nested envelope, so the producer must explicitly select legacy.
        run = subprocess.run
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "packet.jsonl"
            args = argparse.Namespace(
                output=output, host="https://example.invalid", query=["example"],
                collection="", limit=1, api_key="", import_db=True,
            )
            entity = {"id": "company-1", "schema": "Company", "name": "Example Company",
                      "collection_id": "public-records", "properties": {"name": ["Example Company"]}}

            def import_into_temporary_root(command, **kwargs):
                return run([*command, "--root", str(root)], capture_output=True, text=True, **kwargs)

            with mock.patch.object(MODULE, "parse_args", return_value=args), \
                 mock.patch.object(MODULE, "iter_entities", return_value=iter([entity])), \
                 mock.patch.object(MODULE.subprocess, "run", side_effect=import_into_temporary_root):
                self.assertEqual(MODULE.main(), 0)
            document = json.loads(output.read_text())
            stored = root / "db" / document["dtype"] / (document["_id"] + ".ndjson")
            self.assertEqual(json.loads(stored.read_text()), document)

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
