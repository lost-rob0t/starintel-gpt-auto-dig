from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scrape_wef_council_artifacts.py"
SPEC = importlib.util.spec_from_file_location("scrape_wef_council_artifacts", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class WefCouncilArtifactTests(unittest.TestCase):
    def test_extracts_only_official_wef_links_and_classifies_pdf(self) -> None:
        html = """
        <html><body>
          <a href="/publications/pathways-to-digital-justice/">Publication</a>
          <a href="https://www3.weforum.org/docs/example.pdf">Download PDF</a>
          <a href="https://example.com/nope">External</a>
        </body></html>
        """
        links = MODULE.extract_official_links(html, "https://www.weforum.org/people/katherine-hsiao/")
        got = {(item.url, item.kind) for item in links}
        self.assertIn(("https://www.weforum.org/publications/pathways-to-digital-justice/", "publication"), got)
        self.assertIn(("https://www3.weforum.org/docs/example.pdf", "pdf"), got)
        self.assertFalse(any("example.com" in item.url for item in links))

    def test_mentions_are_case_insensitive_and_deduplicated(self) -> None:
        text = "Katherine Hsiao served on a DATA POLICY council. Katherine Hsiao appears twice."
        mentions = MODULE.extract_mentions(text, ["Katherine Hsiao", "Data Policy", "Missing", "Katherine Hsiao"])
        self.assertEqual(mentions, ["Data Policy", "Katherine Hsiao"])

    def test_normalize_url_rejects_non_wef_hosts(self) -> None:
        self.assertIsNone(MODULE.normalize_url("https://www.weforum.org/", "https://example.org/a"))
        self.assertEqual(
            MODULE.normalize_url("https://www.weforum.org/people/x/", "/stories/example/"),
            "https://www.weforum.org/stories/example/",
        )


if __name__ == "__main__":
    unittest.main()
