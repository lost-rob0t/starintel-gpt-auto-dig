from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starintel_doc.model import Document
from starintel_doc.store import validate_repository
from starintel_doc.writer import DatabaseWriteError, canonical_db_path, write_db_document


class CanonicalDatabaseWriterTests(unittest.TestCase):
    def test_writes_exact_db_convention(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = Document.create(
                "org",
                "test",
                doc_id="starintel:org:example",
                data={"name": "Example"},
            ).to_dict()
            target = write_db_document(root, document)
            self.assertEqual(
                target,
                root.resolve() / "db" / "org" / "starintel:org:example.ndjson",
            )
            self.assertTrue(target.read_bytes().endswith(b"\n"))
            self.assertEqual(len(target.read_text(encoding="utf-8").splitlines()), 1)
            self.assertTrue(validate_repository(root)["ok"])

    def test_schema_rejects_path_separator_in_id(self) -> None:
        with self.assertRaises(ValueError):
            Document.create(
                "org",
                "test",
                doc_id="starintel:org:bad/path",
                data={"name": "Bad"},
            )

    def test_canonical_path_preserves_literal_colons(self) -> None:
        document = Document.create(
            "org",
            "test",
            doc_id="starintel:org:example",
            data={"name": "Example"},
        ).to_dict()
        self.assertEqual(
            canonical_db_path(Path("/tmp/starintel-root"), document),
            Path("/tmp/starintel-root/db/org/starintel:org:example.ndjson"),
        )

    def test_requires_replace_for_changed_existing_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = Document.create(
                "org",
                "test",
                doc_id="starintel:org:example",
                data={"name": "Example"},
            ).to_dict()
            write_db_document(root, first)
            changed = dict(first)
            changed["title"] = "Changed"
            with self.assertRaises(DatabaseWriteError):
                write_db_document(root, changed)
            write_db_document(root, changed, replace=True)
            self.assertIn('"title":"Changed"', (root / "db" / "org" / "starintel:org:example.ndjson").read_text())

    def test_rolls_back_unresolved_relation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject = Document.create(
                "org",
                "test",
                doc_id="starintel:org:subject",
                data={"name": "Subject"},
            ).to_dict()
            write_db_document(root, subject)
            relation = Document.create(
                "relation",
                "test",
                doc_id="starintel:relation:subject-missing",
                data={
                    "subject": "starintel:org:subject",
                    "predicate": "related_to",
                    "object": "starintel:org:missing",
                },
            ).to_dict()
            with self.assertRaises(DatabaseWriteError):
                write_db_document(root, relation)
            self.assertFalse(
                (root / "db" / "relation" / "starintel:relation:subject-missing.ndjson").exists()
            )
            self.assertTrue(validate_repository(root)["ok"])


if __name__ == "__main__":
    unittest.main()
