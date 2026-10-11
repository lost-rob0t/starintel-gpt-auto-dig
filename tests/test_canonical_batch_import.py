"""Exercise complete canonical import transactions, including failed writes."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starintel_doc.cli import main
from starintel_doc.store import LocatedDocument, search_documents, validate_repository
from starintel_doc.writer import DatabaseWriteError, write_db_document, write_db_documents


def person(identifier, **fields):
    return {"id": identifier, "dtype": "person", "dataset": "test",
            "schemaVersion": "0.10.1", **fields}


class CanonicalBatchImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a, self.b = person("fixture:a"), person("fixture:b")
        self.relation = {
            "id": "fixture:r", "dtype": "relation", "dataset": "test",
            "schemaVersion": "0.10.1", "predicate": "knows",
            "source": {"id": self.a["id"], "schema": "person"},
            "destination": {"id": self.b["id"], "schema": "person"},
        }

    def records(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.glob("db/*/*.ndjson")}

    def test_cli_import_resolves_forward_references_and_replays_unchanged(self):
        source = self.root / "input.jsonl"
        source.write_text("".join(json.dumps(doc) + "\n"
                                  for doc in [self.relation, self.a, self.b]))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["import", str(source), "--root", str(self.root)]), 0)
            before = self.records()
            self.assertEqual(main(["import", str(source), "--root", str(self.root)]), 0)
        self.assertEqual(before, self.records())
        self.assertEqual(len(before), 3)
        self.assertTrue(validate_repository(self.root)["ok"])

    def test_unresolved_reference_rejects_entire_batch_before_persistence(self):
        with self.assertRaisesRegex(DatabaseWriteError, "before batch write"):
            write_db_documents(self.root, [self.a, self.relation])
        self.assertEqual(self.records(), {})

    def test_late_conflict_and_duplicate_ids_leave_existing_bytes_unchanged(self):
        write_db_document(self.root, self.b)
        before = self.records()
        changed = person("fixture:b", dataset="changed")
        with self.assertRaisesRegex(DatabaseWriteError, "already exists"):
            write_db_documents(self.root, [self.a, changed])
        self.assertEqual(before, self.records())
        with self.assertRaisesRegex(DatabaseWriteError, "duplicate document id"):
            write_db_documents(self.root, [self.a, self.a])
        self.assertEqual(before, self.records())

    def test_failed_late_write_restores_replacements_and_removes_creations(self):
        write_db_document(self.root, self.a)
        before = self.records()
        real_replace = os.replace

        def fail_third_write(source, destination):
            if Path(destination).name == "fixture:r.ndjson":
                raise OSError("injected late write failure")
            return real_replace(source, destination)

        with patch("starintel_doc.writer.os.replace", side_effect=fail_third_write):
            with self.assertRaisesRegex(OSError, "injected"):
                write_db_documents(self.root, [person("fixture:a", dataset="changed"),
                                               self.b, self.relation], replace=True)
        self.assertEqual(before, self.records())
        self.assertFalse(list(self.root.glob("db/*/.*.tmp")))

    def test_successful_replacement_preserves_opaque_extensions(self):
        write_db_document(self.root, self.a)
        changed = person("fixture:a", extensions={"test.provenance": {"raw": [None, "é", 3]}})
        paths = write_db_documents(self.root, [changed], replace=True)
        self.assertEqual(json.loads(paths[0].read_text()), changed)

    def test_canonical_cli_search_filters_and_historical_predicate_fallback(self):
        write_db_documents(self.root, [self.relation, self.a, self.b])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["search", "--root", str(self.root),
                                   "--id", "FIXTURE:R", "--predicate", "KNOWS"]), 0)
        self.assertEqual(json.loads(output.getvalue()), self.relation)
        legacy = {"_id": "legacy:relation", "dtype": "relation",
                  "data": {"predicate": "knows"}}
        located = LocatedDocument(legacy, self.root / "legacy.jsonl")
        self.assertEqual(search_documents([located], doc_id="LEGACY:RELATION",
                                          predicate="KNOWS"), [located])
        self.assertEqual(search_documents([located], predicate="employs"), [])


if __name__ == "__main__":
    unittest.main()
