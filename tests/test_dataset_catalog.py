from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "starintel_site" / "builder.py"
DASHBOARD_JS = ROOT / "site-assets" / "dashboard.js"


class DatasetCatalogTests(unittest.TestCase):
    def test_root_dashboard_lists_every_discovered_dataset(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('output / "datasets.json"', source)
        self.assertIn('Every dataset discovered from canonical StarIntel records.', source)
        self.assertIn('documents.html?dataset=', source)
        self.assertIn('doc.get("dataset") or "unknown"', source)

    def test_document_browser_supports_exact_dataset_links(self) -> None:
        source = DASHBOARD_JS.read_text(encoding="utf-8")
        self.assertIn('params.get("dataset")', source)
        self.assertIn('record.dataset !== requestedDataset', source)
        self.assertIn('Search within ${requestedDataset}', source)


if __name__ == "__main__":
    unittest.main()
