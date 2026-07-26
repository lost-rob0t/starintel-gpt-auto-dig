from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "starintel_site" / "builder.py"
DASHBOARD_JS = ROOT / "site-assets" / "dashboard.js"


class DatasetCatalogTests(unittest.TestCase):
    def test_root_dashboard_lists_source_and_topic_datasets(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('output / "datasets.json"', source)
        self.assertIn('output / "topic-datasets.json"', source)
        self.assertIn("Topic datasets", source)
        self.assertIn("Source datasets", source)
        self.assertIn("excluded_source_dataset", source)

    def test_topic_dataset_has_full_dashboard_and_download(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn("def _write_topic_dataset", source)
        self.assertIn('target = f"dataset-{slug(topic_id)}"', source)
        self.assertIn('downloads / "topic-manifest.json"', source)
        self.assertIn('downloads / "starintel-documents.jsonl"', source)

    def test_document_browser_supports_exact_dataset_links(self) -> None:
        source = DASHBOARD_JS.read_text(encoding="utf-8")
        self.assertIn('params.get("dataset")', source)
        self.assertIn('record.dataset !== requestedDataset', source)
        self.assertIn('Search within ${requestedDataset}', source)


if __name__ == "__main__":
    unittest.main()
