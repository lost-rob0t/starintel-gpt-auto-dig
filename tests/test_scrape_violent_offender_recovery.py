from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "scrape_violent_offender_recovery_fixups.py"
SPEC = importlib.util.spec_from_file_location("violent_recovery_fixups", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_newworld_selects_active_booking_not_first_historical_booking():
    html = """
    <h3>Booking 2024-00000001</h3>
    <div>Booking Date</div><div>01/01/2024</div>
    <div>Release Date</div><div>02/01/2024</div>
    <div>Felonious Assault</div>
    <h3>Booking 2026-00001888</h3>
    <div>Booking Date</div><div>08/08/2026 8:00 PM</div>
    <div>Release Date</div><div></div>
    <div>Scheduled Release Date</div><div></div>
    <div>Booking Origin</div><div>Lima Police Department</div>
    <table><tr><td>1</td><td>Domestic Violence - knowingly cause physical harm</td></tr></table>
    """
    block = MODULE.current_booking_block(html)
    assert MODULE.booking_id(block) == "2026-00001888"
    record = MODULE.recovered_newworld_record(
        "allen", "Example, Person", html, "https://example.test/Inmate/Detail/-1", "2026-08-09T16:00:00Z"
    )
    assert record is not None
    assert record.booking_id == "2026-00001888"
    assert record.violent_charge_matches == ["Domestic Violence - knowingly cause physical harm"]


def test_newworld_supports_split_booking_heading_nodes():
    html = """
    <div>Booking History</div>
    <div>Booking</div><div>2025-00000879</div>
    <div>Booking Date</div><div>04/04/2025 1:18 PM</div>
    <div>Release Date</div><div></div>
    <div>Scheduled Release Date</div><div></div>
    <div>Booking Origin</div><div>Lima Police Department</div>
    <div>Charge Description</div><div>FELONIOUS ASSAULT</div>
    """
    block = MODULE.current_booking_block(html)
    assert MODULE.booking_id(block) == "2025-00000879"
    record = MODULE.recovered_newworld_record(
        "allen", "ALLEN, SHARONIKA DANIELLE", html, "https://example.test/detail", "2026-08-09T16:00:00Z"
    )
    assert record is not None
    assert "FELONIOUS ASSAULT" in record.violent_charge_matches


def test_newworld_uses_latest_booking_when_release_label_is_missing():
    html = """
    <h3>Booking 2025-00000099</h3><div>Felonious Assault</div>
    <h3>Booking 2026-00000101</h3><div>Domestic Violence</div>
    """
    assert MODULE.booking_id(MODULE.current_booking_block(html)) == "2026-00000101"


def test_mahoning_active_roster_builds_detail_urls_without_detail_anchors():
    html = """
    <h3>DOE, JANE</h3>
    <div>Inmate ID: 0077001</div>
    <div>Booking #: 20260809001</div>
    <div>Booking Date: 08/09/2026</div>
    <h3>SMITH, JOHN</h3>
    <div>Inmate ID: 0077002</div>
    <div>Booking #: 20260809002</div>
    """
    entries = MODULE.mahoning_entries(html, "https://pii.mahoningcountyoh.gov/")
    assert entries == [
        ("https://pii.mahoningcountyoh.gov/?bookingID=20260809001&inmateID=0077001", "DOE, JANE"),
        ("https://pii.mahoningcountyoh.gov/?bookingID=20260809002&inmateID=0077002", "SMITH, JOHN"),
    ]


def test_madison_hex_ocv_links_are_discovered():
    html = """
    <a href="/inmateSearch/926d48aac3849e859860a66b2d9bb67a">DOE, JANE</a>
    <a href="/inmateSearch">Search</a>
    """
    assert MODULE.ocv_detail_links(html, "https://www.madisonsheriff.org/inmateSearch", "inmateSearch") == [
        ("https://www.madisonsheriff.org/inmateSearch/926d48aac3849e859860a66b2d9bb67a", "DOE, JANE")
    ]


def test_madison_ocv_detail_record_is_parsed_from_detail_page():
    html = """
    <div>Inmate ID: 47359</div>
    <div>Booked Date: 08/09/2026 11:30 EDT</div>
    <div>Custody Status: IN</div>
    <div>Agency: MCSO</div>
    <div>Charge(s):</div>
    <div>2903.11::FELONIOUS ASSAULT</div>
    """
    record = MODULE.recovery.madison_record(
        "DOE, JANE", html, "https://www.madisonsheriff.org/inmateSearch/123", "2026-08-09T16:00:00Z"
    )
    assert record is not None
    assert record.booking_id == "47359"
    assert record.status == "IN"
    assert record.violent_charge_matches == ["2903.11::FELONIOUS ASSAULT"]


def test_franklin_postback_discovery_finds_select_rows():
    html = """
    <form method="post">
      <input type="hidden" name="__VIEWSTATE" value="abc">
      <a href="javascript:__doPostBack('ctl00$Main$Bookings','Select$3')">View Booking</a>
      <a href="javascript:__doPostBack('ctl00$Main$Pager','Page$2')">2</a>
    </form>
    """
    assert MODULE.recovery.postback_targets(html) == [("ctl00$Main$Bookings", "Select$3")]


def test_summit_html_table_fallback_extracts_violent_row():
    html = """
    <table>
      <tr><td>127713</td><td>IH08O</td><td>ANDERSON, RICHARD E, III</td><td>6/15/1978</td><td>W</td><td>M</td></tr>
      <tr><td>08/28/2026</td><td>14:13:00</td><td>UAPD</td><td>25</td><td>2903.11</td><td>FELONIOUS ASSAULT</td><td>25000</td></tr>
      <tr><td>127714</td><td>IH08P</td><td>SAMPLE, DRUG ONLY</td><td>1/1/1990</td><td>W</td><td>M</td></tr>
      <tr><td>08/29/2026</td><td>09:00:00</td><td>APD</td><td>10</td><td>2925.11</td><td>POSSESSION OF COCAINE</td><td>5000</td></tr>
    </table>
    """
    records, candidates = MODULE.recovery.summit_table_records(html, "2026-08-09T16:00:00Z")
    assert candidates == 2
    assert len(records) == 1
    assert records[0].name == "ANDERSON, RICHARD E, III"
    assert records[0].booking_id == "127713"
    assert "FELONIOUS ASSAULT" in records[0].violent_charge_matches[0]
