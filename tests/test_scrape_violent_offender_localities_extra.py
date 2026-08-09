from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "scrape_violent_offender_localities_extra.py"
SPEC = importlib.util.spec_from_file_location("violent_localities_extra", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_clermont_parser_extracts_booking_case_and_violent_charges():
    html = """
    <html><body>
      <h5>Allen, Daron David - <a href="/jail-inmate-search/1">Details</a></h5>
      <h5>Inmate Information</h5>
      <table><tr><th>DOB</th><th>Sex</th><th>Booking Number</th><th>Booking Date</th></tr>
      <tr><td>03/30/1979</td><td>M</td><td>20261839</td><td>06/03/2026</td></tr></table>
      <h5>Charges</h5>
      <div>1 - 2923.13 Having Weapons While Under Disability</div>
      <div>2 - 2903.11 Felonious Assault</div>
      <table><tr><td>2026 CR 000406</td><td>MILES</td></tr></table>
      <div>3 - 2919.25 Domestic Violence</div>
      <div>4 - 2905.02 Abduction</div>
      <h5>Other, Drug Only - <a href="/jail-inmate-search/2">Details</a></h5>
      <h5>Inmate Information</h5>
      <table><tr><th>DOB</th><th>Sex</th><th>Booking Number</th><th>Booking Date</th></tr>
      <tr><td>01/01/1990</td><td>M</td><td>20260001</td><td>01/01/2026</td></tr></table>
      <h5>Charges</h5><div>1 - Possession of Cocaine</div>
    </body></html>
    """
    records = MODULE.parse_clermont_html(html, "2026-08-09T14:00:00Z")
    assert len(records) == 1
    record = records[0]
    assert record.name == "Allen, Daron David"
    assert record.booking_id == "20261839"
    assert record.booking_date == "06/03/2026"
    assert record.case_numbers == ["2026 CR 000406"]
    assert "2 - 2903.11 Felonious Assault" in record.violent_charge_matches
    assert "3 - 2919.25 Domestic Violence" in record.violent_charge_matches
    assert "4 - 2905.02 Abduction" in record.violent_charge_matches


def test_ocv_link_discovery_extracts_name_and_detail_url():
    html = """
    <h2><a href="/inmateSearch/57173567">Pryor, Daeshawn L</a></h2>
    <a href="/inmateSearch/57173567">View Charges</a>
    <h2><a href="/inmateSearch/57168946">Johnson, David Lee</a></h2>
    """
    assert MODULE.ocv_detail_links(html, "https://example.test/inmateSearch", "inmateSearch") == [
        ("https://example.test/inmateSearch/57173567", "Pryor, Daeshawn L"),
        ("https://example.test/inmateSearch/57168946", "Johnson, David Lee"),
    ]


def test_ocv_detail_parser_filters_nonviolent_record():
    violent = """
    <html><body><div>Inmate ID: 47359</div><div>Booked Date: 07/26/2026 10:59:00 EDT</div>
    <div>Custody Status: IN</div><div>Charges</div><div>Felonious Assault</div></body></html>
    """
    record = MODULE.ocv_detail_record("greene", "Example, Person", violent, "https://example.test/inmateSearch/1", "2026-08-09T14:00:00Z")
    assert record is not None
    assert record.booking_id == "47359"
    assert record.status == "IN"
    assert record.violent_charge_matches == ["Felonious Assault"]

    nonviolent = "<div>Inmate ID: 2</div><div>Possession of Cocaine</div>"
    assert MODULE.ocv_detail_record("greene", "Other, Person", nonviolent, "https://example.test/inmateSearch/2", "2026-08-09T14:00:00Z") is None
