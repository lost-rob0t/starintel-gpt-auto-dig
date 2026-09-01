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


class ImportStarintelCorpusInvariantTests(unittest.TestCase):
    def test_full_collection_has_no_conflicting_duplicate_ids(self) -> None:
        try:
            records = MODULE.collect_all_documents(ROOT)
        except Exception as exc:
            DIAGNOSTIC.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
            raise
        else:
            DIAGNOSTIC.unlink(missing_ok=True)

        self.assertTrue(records)


if __name__ == "__main__":
    unittest.main()
