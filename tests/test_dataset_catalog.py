from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "starintel_site" / "builder.py"
MERGE_GATE = ROOT / "scripts" / "validate-for-merge.py"
DASHBOARD_JS = ROOT / "site-assets" / "dashboard.js"
CORPUS_DASHBOARD = ROOT / "scripts" / "starintel_site" / "corpus_dashboard.py"


class DatasetCatalogTests(unittest.TestCase):
    def test_dataset_catalog_moves_off_root_dashboard(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        dashboard = CORPUS_DASHBOARD.read_text(encoding="utf-8")
        self.assertIn('output / "datasets.json"', source)
        self.assertIn('output / "topic-datasets.json"', source)
        self.assertIn('output / "dataset-catalog.json"', source)
        self.assertIn('output / "datasets.html"', source)
        self.assertIn("def datasets_page", dashboard)
        self.assertIn("Every generated topic dataset and source dataset", dashboard)
        self.assertIn("excluded_source_dataset", source)

    def test_topic_dataset_has_full_dashboard_and_download(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn("def _write_topic_dataset", source)
        self.assertIn('target = f"dataset-{slug(topic_id)}"', source)
        self.assertIn('downloads / "topic-manifest.json"', source)
        self.assertIn('downloads / "starintel-documents.jsonl"', source)

    def test_source_datasets_are_canonical_and_deduplicated_by_generator(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn("def _dataset_key", source)
        self.assertIn("unicodedata.normalize", source)
        self.assertIn("def _write_source_dataset", source)
        self.assertIn('target = f"dataset-source-{slug(dataset)}"', source)
        self.assertIn('downloads / "source-manifest.json"', source)
        self.assertIn("source_documents[source_key]", source)
        self.assertNotIn('"id": f"{target}:{dataset}"', source)

    def test_topic_and_source_nodes_redirect_to_canonical_source_pages(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn("def _topic_node_redirect", source)
        self.assertIn("source_targets_by_id", source)
        self.assertIn('destination = f"../../{source_target}/nodes/{name}.html"', source)

    def test_dataset_page_renders_icon_view_controls_without_text_labels(self) -> None:
        dashboard = CORPUS_DASHBOARD.read_text(encoding="utf-8")
        self.assertIn('aria-label="Card view"', dashboard)
        self.assertIn('aria-label="Table view"', dashboard)
        self.assertIn('data-view="cards"', dashboard)
        self.assertIn('data-view="table"', dashboard)
        self.assertIn('width="18" height="18"', dashboard)
        self.assertNotIn('data-view="cards">Cards</button>', dashboard)
        self.assertNotIn('data-view="table">Table</button>', dashboard)

    def test_merge_gate_reserves_pages_archive_overhead(self) -> None:
        source = MERGE_GATE.read_text(encoding="utf-8")
        self.assertIn("PAGES_CONTENT_BUDGET_BYTES = 9_000_000_000", source)
        self.assertIn("generated content is too large for GitHub Pages", source)

    def test_document_browser_supports_exact_dataset_links(self) -> None:
        source = DASHBOARD_JS.read_text(encoding="utf-8")
        self.assertIn('params.get("dataset")', source)
        self.assertIn('record.dataset !== requestedDataset', source)
        self.assertIn('Search within ${requestedDataset}', source)


if __name__ == "__main__":
    unittest.main()
