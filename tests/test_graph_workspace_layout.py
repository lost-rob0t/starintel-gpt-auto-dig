from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GRAPH_UI = ROOT / "site-assets" / "graph-ui.mjs"


class GraphWorkspaceLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = GRAPH_UI.read_text(encoding="utf-8")

    def test_graph_uses_full_viewport_workspace(self) -> None:
        self.assertIn("width:100vw", self.source)
        self.assertIn("grid-template-columns:minmax(250px,310px) minmax(0,1fr)", self.source)
        self.assertIn('id: "graph-fullscreen"', self.source)

    def test_controls_and_connection_finder_live_in_left_sidebar(self) -> None:
        self.assertIn('tools.id = "graph-tools"', self.source)
        self.assertIn("tools.appendChild(controls)", self.source)
        self.assertIn("tools.appendChild(path)", self.source)
        self.assertIn("position:static!important", self.source)
        self.assertIn("flex-direction:column", self.source)

    def test_sparse_reviewed_corpora_fall_back_to_capped_all_state_backbone(self) -> None:
        self.assertIn("ensureUsefulDefaultReview", self.source)
        self.assertIn('params.set("review", "all")', self.source)
        self.assertIn("reviewed / Math.max(1, total) < 0.02", self.source)


if __name__ == "__main__":
    unittest.main()
