from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import-starintel-documents.py"
DIAGNOSTIC = ROOT / "importer-corpus-error.txt"
SPEC = importlib.util.spec_from_file_location("import_starintel_documents_corpus", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def find_corpus_conflicts() -> list[tuple[str, str, str]]:
    merged: dict[str, object] = {}
    conflicts: list[tuple[str, str, str]] = []

    for path in MODULE.current_document_paths(ROOT):
        relative = path.relative_to(ROOT).as_posix()
        records = MODULE.parse_jsonl(path.read_text(encoding="utf-8"), relative)
        for record in records:
            previous = merged.get(record.document_id)
            if previous is None:
                merged[record.document_id] = record
                continue
            if MODULE.canonical_document(previous.document) == MODULE.canonical_document(record.document):
                continue
            if MODULE.db_source(previous) != MODULE.db_source(record):
                if MODULE.db_source(record):
                    merged[record.document_id] = record
                continue
            old_version = MODULE.integer_version(previous.document)
            new_version = MODULE.integer_version(record.document)
            if old_version is not None and new_version is not None and old_version != new_version:
                if new_version > old_version:
                    merged[record.document_id] = record
                continue
            conflicts.append((record.document_id, previous.source, record.source))

    return conflicts


class ImportStarintelCorpusInvariantTests(unittest.TestCase):
    def test_full_collection_has_no_conflicting_duplicate_ids(self) -> None:
        conflicts = find_corpus_conflicts()
        if conflicts:
            lines = [
                f"ValueError: conflicting duplicate _id {document_id!r}: {source_a} vs {source_b}"
                for document_id, source_a, source_b in conflicts
            ]
            DIAGNOSTIC.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.fail(f"found {len(conflicts)} conflicting duplicate _id records")

        records = MODULE.collect_all_documents(ROOT)
        DIAGNOSTIC.unlink(missing_ok=True)
        self.assertTrue(records)


if __name__ == "__main__":
    unittest.main()
