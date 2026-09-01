import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import-starintel-documents.py"
SPEC = importlib.util.spec_from_file_location("import_starintel_documents", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ImportStarintelCorpusInvariantTests(unittest.TestCase):
    def test_full_collection_has_no_conflicting_duplicate_ids(self) -> None:
        records = MODULE.collect_all_documents(ROOT)
        self.assertTrue(records)


if __name__ == "__main__":
    unittest.main()
