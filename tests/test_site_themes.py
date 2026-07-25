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

    def test_synthwave_uses_dotfile_palette(self) -> None:
        script = (ASSETS / "theme.js").read_text(encoding="utf-8").lower()
        for color in ("#170c32", "#202146", "#92406e", "#fba922", "#2de2e6", "#f3f4f5", "#f6019d", "#62ff00", "#dd546e", "#9700cc"):
            self.assertIn(color, script)

    def test_builder_publishes_theme_runtime_on_every_page(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('shutil.copy2(assets / "theme.js", asset_output / "theme.js")', source)
        self.assertIn('theme_script = f\'<script src="{prefix}assets/theme.js"></script>\'', source)
        self.assertIn('themed(node(doc, target, known), "../../")', source)
        self.assertIn('themed(page(config.get("site_title", "StarIntel GPT Auto Dig"), body), "")', source)

    def test_graph_colors_are_theme_tokens(self) -> None:
        core = (ASSETS / "graph-core.mjs").read_text(encoding="utf-8")
        renderer = (ASSETS / "graph-render.mjs").read_text(encoding="utf-8")
        self.assertIn('person: "--node-person"', core)
        self.assertIn('value("--edge"', renderer)
        self.assertIn('colorFor(node.group || "entity", node.color)', renderer)


if __name__ == "__main__":
    unittest.main()
