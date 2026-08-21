from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest import mock
from urllib.error import HTTPError


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sec_principal_office_history.py"
SPEC = importlib.util.spec_from_file_location("sec_principal_office_history", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SecPrincipalOfficeHistoryTests(unittest.TestCase):
    def test_extracts_8k_principal_executive_office_without_promoting_other_addresses(self) -> None:
        html = """
        <html><body>
          <div>Palantir Technologies Inc.</div>
          <div>518 17th Street, Suite 1015</div>
          <div>Denver, Colorado 80202</div>
          <div>(Address of principal executive offices and zip code)</div>
          <div>1200 17th Street, Floor 15</div>
          <div>Denver, Colorado 80202</div>
          <div>(Former name or former address, if changed since last report)</div>
        </body></html>
        """
        office = MODULE.extract_principal_executive_office(html)
        self.assertEqual(office["street"], "518 17th Street, Suite 1015")
        self.assertEqual(office["city"], "Denver")
        self.assertEqual(office["region"], "Colorado")
        self.assertEqual(office["postal"], "80202")
        self.assertNotIn("1200 17th Street", office["address"])

    def test_extracts_10k_address_when_zip_is_rendered_in_same_cover_row(self) -> None:
        html = """
        <table><tr><td>19505 Biscayne Blvd., Suite 2350</td><td>Aventura, Florida</td><td>33180</td></tr>
        <tr><td>(Address of principal executive offices)</td><td>(Zip Code)</td></tr></table>
        """
        office = MODULE.extract_principal_executive_office(html)
        self.assertEqual(office["street"], "19505 Biscayne Blvd., Suite 2350")
        self.assertEqual(office["city"], "Aventura")
        self.assertEqual(office["region"], "Florida")
        self.assertEqual(office["postal"], "33180")

    def test_missing_marker_is_not_reclassified_as_headquarters(self) -> None:
        html = "<div>Business Address 1200 17TH STREET FLOOR 15 DENVER CO 80202</div>"
        with self.assertRaisesRegex(ValueError, "principal executive offices"):
            MODULE.extract_principal_executive_office(html)

    def test_observation_preserves_sec_semantics_and_filing_provenance(self) -> None:
        office = {
            "address": "19505 Biscayne Blvd., Suite 2350, Aventura, Florida 33180",
            "street": "19505 Biscayne Blvd., Suite 2350",
            "city": "Aventura",
            "region": "Florida",
            "postal": "33180",
            "country": "United States",
        }
        item = MODULE.office_observation(
            org_id="starintel:org:palantir-technologies-inc",
            office=office,
            form="8-K",
            filing_date="2026-06-03",
            accession="0001321655-26-000033",
            filing_url="https://www.sec.gov/Archives/edgar/data/1321655/000132165526000033/pltr-20260603.htm",
            retrieved_at="2026-08-17T22:30:00Z",
        )
        self.assertEqual(item["observation_type"], "sec_reported_principal_executive_office")
        self.assertEqual(item["value"]["location_type"], "principal_executive_office")
        self.assertEqual(item["value"]["filing_date"], "2026-06-03")
        self.assertEqual(item["value"]["accession"], "0001321655-26-000033")
        self.assertNotIn("headquarters", item["value"])

    def test_retry_honors_retry_after_for_429(self) -> None:
        error = HTTPError("https://www.sec.gov/x", 429, "rate limited", {"Retry-After": "2"}, None)
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"<html>ok</html>"
        opener = mock.Mock(side_effect=[error, response])
        sleeper = mock.Mock()
        text = MODULE.fetch_text("https://www.sec.gov/x", opener=opener, sleeper=sleeper, attempts=2)
        self.assertEqual(text, "<html>ok</html>")
        sleeper.assert_called_once_with(2.0)

    def test_deduplicate_history_is_idempotent_and_keeps_changed_addresses(self) -> None:
        first = {"address": "1200 17th Street, Floor 15, Denver, Colorado 80202", "filing_date": "2025-11-03"}
        same = {"address": first["address"], "filing_date": "2025-11-03"}
        changed = {"address": "518 17th Street, Suite 1015, Denver, Colorado 80202", "filing_date": "2026-02-02"}
        self.assertEqual(MODULE.deduplicate_history([first, same, changed]), [first, changed])


if __name__ == "__main__":
    unittest.main()
