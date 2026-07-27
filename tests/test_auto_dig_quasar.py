from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "build-auto-dig-quasar.py"
spec = importlib.util.spec_from_file_location("build_auto_dig_quasar", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class AutoDigQuasarBuildTest(unittest.TestCase):
    def test_embeds_exact_pinned_build_and_patches_navigation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "site").mkdir()
            (root / "site" / "index.html").write_text("<nav><a>Research</a></nav>")
            (root / "dist").mkdir()
            (root / "dist" / "index.html").write_text("<div id='root'></div>")
            args = Namespace(
                auto_dig_root=str(root),
                site_dir=str(root / "site"),
                quasar_dist=str(root / "dist"),
                quasar_fork_commit="a" * 40,
                quasar_upstream_commit="b" * 40,
                auto_dig_version="0.9.0",
                starintel_schema_version="0.9.0",
                correction_repository="lost-rob0t/starintel-gpt-auto-dig",
            )
            output = module.build(args)
            self.assertTrue((output / "app" / "index.html").exists())
            lock = json.loads((root / "quasar-fork.lock.json").read_text())
            self.assertEqual(lock["quasar_fork_commit"], "a" * 40)
            self.assertIn("data-auto-dig-quasar", (root / "site" / "index.html").read_text())

    def test_shell_uses_sandbox_and_typed_host(self):
        html = module.shell_html(
            correction_repository="owner/repo",
            versions={
                "auto_dig_version": "1",
                "quasar_fork_commit": "a" * 40,
                "quasar_upstream_commit": "b" * 40,
                "starintel_schema_version": "0.9.0",
            },
        )
        self.assertIn("sandbox=", html)
        self.assertNotIn("allow-top-navigation", html)
        self.assertIn("host.js", html)


if __name__ == "__main__":
    unittest.main()
