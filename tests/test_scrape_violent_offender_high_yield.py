from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "scrape_violent_offender_high_yield.py"
SPEC = importlib.util.spec_from_file_location("violent_high_yield", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_newworld_page_count_and_detail_links():
    html = """
    <div>Showing 1 to 100 of 217</div>
    <a href="/NewWorld.InmateInquiry/OH0020000/Inmate/Detail/-123">Smith, Jane Ann</a>
    <a href="/NewWorld.InmateInquiry/OH0020000/Inmate/Detail/-123"><img alt="photo"></a>
    """
    assert MODULE.newworld_page_count(html) == 3
    assert MODULE.newworld_detail_links(html, "https://example.test/NewWorld.InmateInquiry/OH0020000") == [
        ("https://example.test/NewWorld.InmateInquiry/OH0020000/Inmate/Detail/-123", "Smith, Jane Ann")
    ]


def test_newworld_record_uses_current_booking_only():
    html = """
    <h1>Inmate Detail - Example, Person</h1>
    <h3>Booking 2026-00000945</h3>
    <div>Booking Date</div><div>06/18/2026 5:50 PM</div>
    <div>Release Date</div><div></div>
    <div>Booking Origin</div><div>County Sheriff's Office</div>
    <table><tr><th>Number</th><th>Charge Description</th><th>Docket Number</th></tr>
    <tr><td>1</td><td>Felonious Assault</td><td>2026CR00427</td></tr></table>
    <h3>Booking 2025-00000001</h3>
    <div>Booking Date</div><div>01/01/2025</div>
    <div>Possession of Cocaine</div>
    """
    record = MODULE.newworld_record(
        "muskingum",
        "Example, Person",
        html,
        "https://example.test/detail/1",
        "2026-08-09T14:00:00Z",
    )
    assert record is not None
    assert record.booking_id == "2026-00000945"
    assert record.booking_date == "06/18/2026 5:50 PM"
    assert record.violent_charge_matches == ["Felonious Assault"]
    assert "2026CR00427" in record.case_numbers


def test_newworld_does_not_promote_old_violent_booking():
    html = """
    <h3>Booking 2026-00000945</h3>
    <div>Booking Date</div><div>06/18/2026 5:50 PM</div>
    <div>Possession of Cocaine</div>
    <h3>Booking 2025-00000001</h3>
    <div>Booking Date</div><div>01/01/2025</div>
    <div>Felonious Assault</div>
    """
    assert MODULE.newworld_record(
        "allen",
        "Example, Person",
        html,
        "https://example.test/detail/1",
        "2026-08-09T14:00:00Z",
    ) is None


def test_mahoning_links_and_detail_record():
    listing = """
    <a href="/?bookingID=20260616013&inmateID=0077240">Details</a>
    <a href="/?recentBooking=true">Recent</a>
    """
    links = MODULE.mahoning_detail_links(listing, "https://pii.example.test/")
    assert links == ["https://pii.example.test/?bookingID=20260616013&inmateID=0077240"]

    detail = """
    <div>Inmate Name: SAMPLE, PERSON</div>
    <div>Booking Number: 20260616013</div>
    <div>Arresting Agency: SAMPLE POLICE DEPT.</div>
    <div>Booking Date: 06/16/2026</div>
    <div>Release Date:</div>
    <div>Status: CP - CUSTODY PRETRIAL</div>
    <h4>Offense: Assault on Peace Officer</h4>
    <div>Date of Arrest: 06/16/2026</div>
    """
    record = MODULE.mahoning_record(detail, links[0], "2026-08-09T14:00:00Z")
    assert record is not None
    assert record.name == "SAMPLE, PERSON"
    assert record.booking_id == "20260616013"
    assert record.arresting_agency == "SAMPLE POLICE DEPT."
    assert "Offense: Assault on Peace Officer" in record.violent_charge_matches
