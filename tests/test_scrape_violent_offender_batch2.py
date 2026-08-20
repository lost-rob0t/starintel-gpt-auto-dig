from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "scrape_violent_offender_batch2.py"
SPEC = importlib.util.spec_from_file_location("violent_batch2", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_lorain_current_booking_parser():
    html = """
    <h3>Booking 2026-00209829</h3>
    <div>Booking Date</div><div>6/29/2026 4:22 AM</div>
    <div>Release Date</div><div></div>
    <div>Booking Origin</div><div>Lorain County Sheriff's Office</div>
    <table>
      <tr><th>Number</th><th>Charge Description</th><th>Docket Number</th></tr>
      <tr><td>1</td><td>Felonious Assault</td><td>26CR115432</td></tr>
    </table>
    <h3>Booking 2025-00200000</h3>
    <div>Possession of Cocaine</div>
    """
    record = MODULE.lorain_record(
        "SAMPLE, PERSON",
        html,
        "https://example.test/Default/Inmate/Detail/-1",
        "2026-08-09T14:00:00Z",
    )
    assert record is not None
    assert record.booking_id == "2026-00209829"
    assert record.booking_date == "6/29/2026 4:22 AM"
    assert record.arresting_agency == "Lorain County Sheriff's Office"
    assert record.case_numbers == ["26CR115432"]
    assert record.violent_charge_matches == ["Felonious Assault"]


def test_summit_roster_parser_filters_to_violent_blocks():
    text = """
Summit County Sheriff's Office
Head Count With Photos Report
127713 IH08O ANDERSON, RICHARD E, III 6/15/1978 W M
Arrest Date / Time Agency Officer Statute Statute Description Bail/Bond
08/28/2026 14:13:00 UAPD 25 2903.11 FELONIOUS ASSAULT 25000
08/28/2026 14:13:00 UAPD 25 2923.13 HAVING WEAPONS UNDER DISABILITY 0
127714 IH08P SAMPLE, DRUG ONLY 1/1/1990 W M
Arrest Date / Time Agency Officer Statute Statute Description Bail/Bond
08/29/2026 09:00:00 APD 10 2925.11 POSSESSION OF COCAINE 5000
    """
    records = MODULE.summit_records(text, "2026-08-09T14:00:00Z")
    assert len(records) == 1
    record = records[0]
    assert record.name == "ANDERSON, RICHARD E, III"
    assert record.booking_id == "127713"
    assert record.arrest_date == "08/28/2026 14:13:00"
    assert record.arresting_agency == "UAPD"
    assert record.status == "current"
    assert record.violent_charge_matches == [
        "08/28/2026 14:13:00 UAPD 25 2903.11 FELONIOUS ASSAULT 25000"
    ]


def test_summit_roster_can_parse_pdf_or_html_text_path():
    html = b"<html><body><div>127713 IH08O ANDERSON, RICHARD E, III 6/15/1978 W M</div></body></html>"
    assert "ANDERSON, RICHARD" in MODULE.response_text(html, "text/html")
