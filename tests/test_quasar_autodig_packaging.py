from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class QuasarAutoDigPackagingTests(unittest.TestCase):
    def test_project_declares_live_websocket_client_dependency(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)["project"]

        dependencies = project.get("dependencies", [])
        self.assertIn("websocket-client>=1.9,<2", dependencies)


if __name__ == "__main__":
    unittest.main()
