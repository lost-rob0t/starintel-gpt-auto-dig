from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site-assets"
BUILDER = ROOT / "scripts" / "starintel_site" / "builder.py"
DASHBOARD = ROOT / "scripts" / "starintel_site" / "dashboard.py"


class DashboardGraphTests(unittest.TestCase):
    def test_builder_emits_separate_dashboard_and_graph_pages(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('(target_out / "graph.html").write_text', source)
        self.assertIn('(target_out / "documents.html").write_text', source)
        self.assertIn('(target_out / "documents.json").write_text', source)

    def test_graph_defaults_to_reviewed_backbone(self) -> None:
        source = (ASSETS / "graph-explorer.mjs").read_text(encoding="utf-8")
        self.assertIn('mode: "backbone"', source)
        self.assertIn('review.value = params.get("review")', source)
        self.assertIn("MAX_BACKBONE = 140", source)
        self.assertIn("MAX_FOCUS = 380", source)
        self.assertIn('document.getElementById("graph-dataset")', source)

    def test_renderer_has_level_of_detail_budget(self) -> None:
        source = (ASSETS / "graph-render-scaled.mjs").read_text(encoding="utf-8")
        self.assertIn("view.scale < 0.55", source)
        self.assertIn("const budget = view.scale < 0.3 ? 2600 : 7000", source)
        self.assertIn("if (!this.onScreen(a, 140) && !this.onScreen(b, 140)) return", source)

    def test_review_state_is_conservative(self) -> None:
        source = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn('return "unreviewed"', source)
        self.assertIn('"verified"', source)
        self.assertIn('"pending"', source)
        self.assertIn('node["reviewed"] = reviewed', source)
        self.assertIn('edge["reviewed"] = reviewed', source)


if __name__ == "__main__":
    unittest.main()
