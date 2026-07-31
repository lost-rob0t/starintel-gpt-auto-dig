from __future__ import annotations

import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "build-auto-dig-quasar.py"
spec = importlib.util.spec_from_file_location("build_auto_dig_quasar", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


VERSIONS = {
    "auto_dig_version": "0.9.0",
    "quasar_commit": "a" * 40,
    "quasar_ui_commit": "b" * 40,
    "starintel_schema_version": "0.9.0",
}


class AutoDigQuasarBuildTest(unittest.TestCase):
    def test_shell_is_only_the_graph_editor_frame(self):
        rendered = module.shell_html(
            correction_repository="owner/repo",
            versions=VERSIONS,
        )

        self.assertIn('id="quasar-frame"', rendered)
        self.assertIn('src="app/index.html?host=auto-dig"', rendered)
        self.assertIn("host.js", rendered)
        self.assertIn("sandbox=", rendered)
        self.assertNotIn("allow-top-navigation", rendered)
        self.assertNotIn("<header", rendered)
        self.assertNotIn("data-quasar-route", rendered)

    def test_graph_entrypoints_redirect_to_quasar_with_dataset(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            (site / "quasar").mkdir()
            (site / "quasar" / "index.html").write_text("quasar", encoding="utf-8")
            (site / "graph.html").write_text("legacy root graph", encoding="utf-8")
            (site / "palantir").mkdir()
            (site / "palantir" / "graph.html").write_text(
                "legacy dataset graph",
                encoding="utf-8",
            )

            patched = module.patch_graph_entrypoints(site)

            self.assertEqual(len(patched), 2)
            root_graph = (site / "graph.html").read_text(encoding="utf-8")
            dataset_graph = (site / "palantir" / "graph.html").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "quasar/index.html?dataset=complete-corpus",
                root_graph,
            )
            self.assertIn(
                "../quasar/index.html?dataset=palantir",
                dataset_graph,
            )
            self.assertNotIn("legacy root graph", root_graph)
            self.assertNotIn("legacy dataset graph", dataset_graph)

    def test_build_copies_quasar_and_replaces_legacy_graph_page(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            site = root / "site"
            dist = root / "dist"
            (site / "example").mkdir(parents=True)
            (site / "example" / "graph.html").write_text(
                "old graph UI",
                encoding="utf-8",
            )
            dist.mkdir()
            (dist / "index.html").write_text(
                "<div id='root'></div>",
                encoding="utf-8",
            )

            output = module.build(
                Namespace(
                    auto_dig_root=str(root),
                    site_dir=str(site),
                    quasar_dist=str(dist),
                    correction_repository="owner/repo",
                    **VERSIONS,
                )
            )

            self.assertTrue((output / "app" / "index.html").is_file())
            self.assertTrue((output / "host.js").is_file())
            self.assertTrue((output / "version.json").is_file())
            redirect = (site / "example" / "graph.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("../quasar/index.html?dataset=example", redirect)
            self.assertNotIn("old graph UI", redirect)

    def test_host_seeds_quasar_and_navigates_after_runtime_subscription(self):
        host = (Path(__file__).parents[1] / "scripts" / "auto_dig_quasar_host.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('const GRAPH_ROUTE = "/graph"', host)
        self.assertIn("navigateToGraphAfterDatasetLoad();", host)
        self.assertIn("const dataset = await loadDataset(id);", host)
        handshake = host.split("handshake: async", 1)[1].split(
            "getActiveDatasetId", 1
        )[0]
        self.assertNotIn('notify("navigate"', handshake)
        self.assertIn("starintel-complete-corpus.jsonl", host)
        self.assertIn("starintel-documents.jsonl", host)
        self.assertNotIn("indexedDB.open", host)
        self.assertNotIn("data-quasar-route", host)


if __name__ == "__main__":
    unittest.main()
