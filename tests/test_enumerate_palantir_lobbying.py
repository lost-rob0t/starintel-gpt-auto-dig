from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "enumerate_palantir_lobbying.py"
SPEC = importlib.util.spec_from_file_location("palantir_lobbying", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def filing(uuid: str, filing_type: str, posted: str, amount: str) -> dict:
    return {
        "filing_uuid": uuid,
        "filing_type": filing_type,
        "filing_type_display": "1st Quarter - Amendment" if filing_type.endswith("A") else "1st Quarter - Report",
        "filing_year": 2026,
        "filing_period": "first_quarter",
        "filing_period_display": "1st Quarter",
        "dt_posted": posted,
        "income": amount,
        "expenses": None,
        "registrant": {"id": 10, "name": "Outside Firm LLC"},
        "client": {"id": 20, "name": "Palantir Technologies Inc."},
        "lobbying_activities": [],
    }


def test_collapse_amendments_uses_latest_posted_version() -> None:
    original = filing("old", "Q1", "2026-04-20T10:00:00Z", "100000")
    amendment = filing("new", "Q1A", "2026-05-01T10:00:00Z", "120000")
    active, superseded = MODULE.collapse_amendments([amendment, original])
    assert [item["filing_uuid"] for item in active] == ["new"]
    assert [item["filing_uuid"] for item in superseded] == ["old"]


def test_filing_amount_uses_expense_for_in_house() -> None:
    item = filing("self", "Q1", "2026-04-20T10:00:00Z", "")
    item["registrant"] = {"id": 1, "name": "Palantir Technologies, Inc."}
    item["client"] = {"id": 2, "name": "Palantir Technologies Inc."}
    item["expenses"] = "1980000.00"
    amount, basis = MODULE.filing_amount(item)
    assert amount == Decimal("1980000.00")
    assert basis == "expenses"


def test_extract_activities_normalizes_people_entities_and_issues() -> None:
    item = filing("activity", "Q1", "2026-04-20T10:00:00Z", "40000")
    item["lobbying_activities"] = [{
        "general_issue_code": "DEF",
        "general_issue": "Defense",
        "description": "FY2027 NDAA and software procurement",
        "government_entities": [{"name": "U.S. Department of Defense"}, {"name": "U.S. Senate"}],
        "lobbyists": [{"first_name": "Jane", "last_name": "Doe", "covered_position": "Former committee staff"}],
    }]
    activities = MODULE.extract_activities(item)
    assert activities[0]["general_issue_code"] == "DEF"
    assert activities[0]["specific_issues"] == "FY2027 NDAA and software procurement"
    assert activities[0]["government_entities"] == ["U.S. Department of Defense", "U.S. Senate"]
    assert activities[0]["lobbyists"][0]["name"] == "Jane Doe"


def test_summary_does_not_double_count_superseded_filings() -> None:
    original = filing("old", "Q1", "2026-04-20T10:00:00Z", "100000")
    amendment = filing("new", "Q1A", "2026-05-01T10:00:00Z", "120000")
    active, superseded = MODULE.collapse_amendments([original, amendment])
    summary = MODULE.summarize(active, len(superseded))
    assert summary["disclosed_amount_total"] == 120000
    assert summary["superseded_filing_count"] == 1
