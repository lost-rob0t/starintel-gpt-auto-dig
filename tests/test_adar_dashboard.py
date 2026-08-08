from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.starintel_site.corpus_dashboard import dashboard_projection, dataset_metrics

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "starintel_site" / "builder.py"
SHELL = ROOT / "site-assets" / "adar-shell.js"
DASHBOARD_JS = ROOT / "site-assets" / "corpus-dashboard.js"
DASHBOARD_CSS = ROOT / "site-assets" / "adar-dashboard.css"


class AdarDashboardTests(unittest.TestCase):
    def sample_docs(self) -> list[dict]:
        return [
            {
                "_id": "starintel:person:alice",
                "dtype": "person",
                "dataset": "demo",
                "title": "Alice Example",
                "date_added": "2026-08-01T00:00:00Z",
                "date_updated": "2026-08-08T00:00:00Z",
                "sources": [{"url": "https://example.com/alice"}],
                "verification": {"status": "verified"},
                "data": {"name": "Alice Example"},
            },
            {
                "_id": "starintel:org:example",
                "dtype": "org",
                "dataset": "demo",
                "title": "Example Org",
                "date_added": "2026-08-02T00:00:00Z",
                "date_updated": "2026-08-08T00:00:00Z",
                "sources": [{"url": "https://example.com/org"}],
                "verification": {"status": "verified"},
                "data": {"name": "Example Org"},
            },
            {
                "_id": "starintel:relation:alice-example",
                "dtype": "relation",
                "dataset": "demo",
                "title": "Alice works at Example",
                "date_added": "2026-08-03T00:00:00Z",
                "date_updated": "2026-08-08T00:00:00Z",
                "sources": [{"url": "https://example.com/relation"}],
                "verification": {"status": "verified"},
                "data": {
                    "subject": "starintel:person:alice",
                    "object": "starintel:org:example",
                    "predicate": "employed_by",
                },
            },
            {
                "_id": "starintel:claim:finding",
                "dtype": "claim",
                "dataset": "demo",
                "title": "Evidence-backed finding",
                "summary": "A reviewed finding with evidence.",
                "date_added": "2026-08-04T00:00:00Z",
                "date_updated": "2026-08-08T00:00:00Z",
                "sources": [{"url": "https://example.com/finding"}],
                "evidence": [{"id": "e1"}],
                "assessment": {"confidence": 0.95},
                "verification": {"status": "verified"},
                "data": {"claim": "Evidence-backed finding"},
            },
        ]

    def test_projection_separates_document_and_relation_types(self) -> None:
        docs = self.sample_docs()
        catalog = [{"kind": "source", "id": "demo", "title": "demo", "record_count": 4, "source_count": 4, "added_30d": 4}]
        search = [{"id": doc["_id"], "url": f"demo/nodes/{index}.html"} for index, doc in enumerate(docs)]
        projection = dashboard_projection(docs, catalog, search)
        document_labels = {row["label"] for row in projection["document_types"]}
        relation_labels = {row["label"] for row in projection["relation_types"]}
        self.assertNotIn("relation", document_labels)
        self.assertIn("employed by", relation_labels)
        self.assertEqual(projection["top_connected_people"][0]["name"], "Alice Example")
        self.assertEqual(projection["top_findings"][0]["title"], "Evidence-backed finding")

    def test_dataset_metrics_include_analyst_counts(self) -> None:
        metrics = dataset_metrics(self.sample_docs())
        self.assertEqual(metrics["people_count"], 1)
        self.assertEqual(metrics["organization_count"], 1)
        self.assertEqual(metrics["relation_count"], 1)
        self.assertEqual(metrics["source_count"], 4)
        self.assertGreater(metrics["added_30d"], 0)

    def test_builder_emits_dashboard_and_dedicated_dataset_page(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('output / "dashboard-data.json"', source)
        self.assertIn('output / "dataset-catalog.json"', source)
        self.assertIn('output / "datasets.html"', source)
        self.assertNotIn('topic_cards = "".join', source)

    def test_cross_site_navigation_is_explicit_and_preserves_local_tools(self) -> None:
        shell = SHELL.read_text(encoding="utf-8")
        self.assertIn("https://auto-research.starintel.actor/", shell)
        self.assertIn('"Dashboard"', shell)
        self.assertIn('"Datasets"', shell)
        self.assertIn('"Research ↗"', shell)
        self.assertIn("localLinks", shell)
        self.assertIn('link.label === "Dashboard" ? "Dataset" : link.label', shell)

    def test_dashboard_assets_are_dependency_free_and_accessible(self) -> None:
        javascript = DASHBOARD_JS.read_text(encoding="utf-8")
        css = DASHBOARD_CSS.read_text(encoding="utf-8")
        self.assertNotIn("cdn", javascript.lower())
        self.assertIn('role: "img"', javascript)
        self.assertIn("chart-fallback", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("IBM Plex Sans", css)


if __name__ == "__main__":
    unittest.main()
