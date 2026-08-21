from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scrape_violent_offender_localities.py"
SPEC = importlib.util.spec_from_file_location("violent_localities", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_licking_parser_keeps_violent_charge_and_drops_drug_only_record():
    html = """
    <html><body>
      <div>ABBOTT, JOSHUA A</div><div>Booking#</div><div>2026-00001860</div>
      <div>In Date</div><div>7/7/2026</div><div>Arresting Agency</div><div>ACS</div>
      <div>Docket#</div><div>Charges</div><div>25CR644</div><div>Receiving Stolen Property (F4)</div>
      <div>BROWN, CORNELIUS N</div><div>Booking#</div><div>2026-00001565</div>
      <div>In Date</div><div>6/7/2026</div><div>Arresting Agency</div><div>NPD</div>
      <div>Docket#</div><div>Charges</div><div>26CR383</div><div>Attempted Murder (F1)</div>
    </body></html>
    """
    records = MODULE.parse_licking_html(html, "2026-08-09T13:00:00Z")
    assert len(records) == 1
    assert records[0].name == "BROWN, CORNELIUS N"
    assert records[0].booking_id == "2026-00001565"
    assert records[0].case_numbers == ["26CR383"]
    assert records[0].violent_charge_matches == ["Attempted Murder (F1)"]


def test_madison_parser_extracts_booking_and_charge():
    html = """
    <html><body>
      <h2>DOE, JANE</h2>
      <div>Sun, Aug 9, 2026</div>
      <div>Inmate Details:</div>
      <div>Booking Details:</div>
      <div>Booking Date: 08/09/2026</div>
      <div>Booking Number: 107999</div>
      <div>Agency: MCSO</div>
      <div>Charge(s):</div>
      <div>2903.11::FELONIOUS ASSAULT</div>
    </body></html>
    """
    records = MODULE.parse_madison_html(html, "2026-08-09T13:00:00Z")
    assert len(records) == 1
    assert records[0].name == "DOE, JANE"
    assert records[0].booking_id == "107999"
    assert records[0].violent_charge_matches == ["2903.11::FELONIOUS ASSAULT"]


def test_lucas_text_parser_extracts_violent_booking():
    text = """
Lucas County Corrections Center
Gardner, Temicheal Daniel Book Dttm: 08/08/2026 04:51
Charge Court Charge
1-1 Toledo Municipal Court Felonious Assault Weapon Or Ordnance
2-1 Toledo Municipal Court Felonious Assault Weapon Or Ordnance
Arresting Agency: Toledo Police Department Arrest Dttm: 08/08/2026 01:20
Current Status: Active
Other, Person Book Dttm: 08/08/2026 05:00
Charge Court Charge
1-1 Toledo Municipal Court Possession Of Controlled Substances
Arresting Agency: Toledo Police Department Arrest Dttm: 08/08/2026 04:30
Current Status: Active
    """
    records = MODULE.parse_lucas_text(text, "2026-08-09T13:00:00Z")
    assert len(records) == 1
    assert records[0].name == "Gardner, Temicheal Daniel"
    assert records[0].arresting_agency == "Toledo Police Department"
    assert records[0].status == "Active"
    assert records[0].violent_charge_matches == [
        "1-1 Toledo Municipal Court Felonious Assault Weapon Or Ordnance",
        "2-1 Toledo Municipal Court Felonious Assault Weapon Or Ordnance",
    ]


def test_detail_link_discovery_supports_franklin_and_hamilton():
    html = """
    <a href="BookingDetail.aspx?BookingID=123">Franklin detail</a>
    <a href="/justice-center-services/inmate-search/inmate-detail/?id=456">Hamilton detail</a>
    <a href="BookingFind.aspx">search</a>
    """
    links = MODULE.search_detail_links(html, "https://example.test/Publicview/")
    assert links == [
        "https://example.test/Publicview/BookingDetail.aspx?BookingID=123",
        "https://example.test/justice-center-services/inmate-search/inmate-detail/?id=456",
    ]


def test_violent_classifier_does_not_match_drug_possession():
    assert MODULE.violent_lines(["Possession of Drugs", "Felonious Assault"]) == ["Felonious Assault"]
