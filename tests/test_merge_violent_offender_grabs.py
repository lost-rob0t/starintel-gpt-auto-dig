from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "merge_violent_offender_grabs.py"
SPEC = importlib.util.spec_from_file_location("violent_merge", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_coalesce_sources_prefers_successful_recovery_over_stale_zero():
    groups = [
        (
            "primary",
            [],
            {"sources": [{"source": "franklin", "records": 0, "candidates_seen": 0, "pages_fetched": 28, "error": None}]},
        ),
        (
            "recovered",
            [],
            {"sources": [{"source": "franklin", "records": 17, "candidates_seen": 80, "pages_fetched": 90, "error": None}]},
        ),
    ]
    assert MODULE.coalesce_sources(groups) == [
        {"source": "franklin", "records": 17, "candidates_seen": 80, "pages_fetched": 90, "error": None}
    ]


def test_coalesce_sources_keeps_success_over_later_error():
    groups = [
        (
            "primary",
            [],
            {"sources": [{"source": "summit", "records": 2, "candidates_seen": 100, "pages_fetched": 1, "error": None}]},
        ),
        (
            "recovered",
            [],
            {"sources": [{"source": "summit", "records": 0, "candidates_seen": 0, "pages_fetched": 0, "error": "timeout"}]},
        ),
    ]
    assert MODULE.coalesce_sources(groups)[0]["records"] == 2
    assert MODULE.coalesce_sources(groups)[0]["error"] is None
