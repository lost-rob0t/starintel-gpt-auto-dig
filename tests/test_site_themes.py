from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "site-assets"
BUILDER = ROOT / "scripts" / "starintel_site" / "builder.py"


class SiteThemeTests(unittest.TestCase):
    def test_required_themes_are_registered(self) -> None:
        script = (ASSETS / "theme.js").read_text(encoding="utf-8")
        for theme in (
            "midnight",
            "hacker-green",
            "synthwave-outrun",
            "black-gold",
            "yotsuba-pol",
            "nord",
            "dracula",
            "solarized-dark",
            "gruvbox",
            "paper",
        ):
            self.assertIn(f'id: "{theme}"', script)

    def test_black_gold_is_the_canonical_default(self) -> None:
        script = (ASSETS / "theme.js").read_text(encoding="utf-8")
        self.assertIn('const DEFAULT_THEME = "black-gold";', script)
        self.assertNotIn('const DEFAULT_THEME = "midnight";', script)

    def test_synthwave_uses_dotfile_palette(self) -> None:
        script = (ASSETS / "theme.js").read_text(encoding="utf-8").lower()
        for color in ("#170c32", "#202146", "#92406e", "#fba922", "#2de2e6", "#f3f4f5", "#f6019d", "#62ff00", "#dd546e", "#9700cc"):
            self.assertIn(color, script)

    def test_builder_publishes_theme_and_adar_runtime_on_every_page(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('"theme.js",', source)
        self.assertIn('"adar-dashboard.css",', source)
        self.assertIn('"adar-shell.js",', source)
        self.assertIn('"corpus-dashboard.js",', source)
        self.assertIn('theme_script = f\'<script src="{prefix}assets/theme.js"></script>\'', source)
        self.assertIn('shell_script = f\'<script defer src="{prefix}assets/adar-shell.js"></script>\'', source)
        self.assertIn('themed(node(doc, target, known), "../../")', source)
        self.assertIn('themed(root_dashboard_page(projection, site_title), "")', source)
        self.assertIn('themed(datasets_page(catalog, site_title), "")', source)

    def test_graph_colors_are_theme_tokens(self) -> None:
        core = (ASSETS / "graph-core.mjs").read_text(encoding="utf-8")
        renderer = (ASSETS / "graph-render.mjs").read_text(encoding="utf-8")
        self.assertIn('person: "--node-person"', core)
        self.assertIn('value("--edge"', renderer)
        self.assertIn('colorFor(node.group || "entity", node.color)', renderer)


if __name__ == "__main__":
    unittest.main()