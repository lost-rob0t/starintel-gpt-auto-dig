#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEGACY_BUILDER = ROOT / "scripts" / "build_research_site.py"


def load_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("starintel_build_research_site", LEGACY_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load site builder: {LEGACY_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_fast_materializer(module: ModuleType) -> None:
    original = module.materialize_input

    def materialize_input(
        digs_root: Path,
        db_root: Path,
        workspace: Path,
        config: dict[str, Any],
    ) -> None:
        executable = os.environ.get("STARINTEL_SITE_MATERIALIZER")
        corpus_validated = os.environ.get("STARINTEL_CORPUS_VALIDATED") == "1"
        if not executable or not corpus_validated:
            original(digs_root, db_root, workspace, config)
            return

        materializer = Path(executable)
        if not materializer.is_file():
            raise RuntimeError(f"Nim site materializer not found: {materializer}")

        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        if digs_root.exists():
            shutil.copytree(digs_root, workspace, dirs_exist_ok=True)

        module.filter_excluded(workspace, config)
        subprocess.run(
            [
                str(materializer),
                "--db",
                str(db_root),
                "--workspace",
                str(workspace),
                "--config",
                str(module.ROOT / "site-config.json"),
            ],
            cwd=module.ROOT,
            check=True,
        )

    module.materialize_input = materialize_input


def main() -> int:
    module = load_builder()
    install_fast_materializer(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
