from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sec_principal_office_history.py"
SPEC = importlib.util.spec_from_file_location("sec_principal_office_history_real_cover", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SecPrincipalOfficeRealCoverShapeTests(unittest.TestCase):
    def test_extracts_combined_street_city_region_cell_with_separate_zip(self) -> None:
        html = """
        <table>
          <tr>
            <td>19505 Biscayne Blvd., Suite 2350 Aventura, Florida</td>
            <td>33180</td>
          </tr>
          <tr>
            <td>(Address of principal executive offices)</td>
            <td>(Zip Code)</td>
          </tr>
        </table>
        """
        office = MODULE.extract_principal_executive_office(html)
        self.assertEqual(office["street"], "19505 Biscayne Blvd., Suite 2350")
        self.assertEqual(office["city"], "Aventura")
        self.assertEqual(office["region"], "Florida")
        self.assertEqual(office["postal"], "33180")

    def test_extracts_effective_company_principal_office_notice(self) -> None:
        html = """
        <html><body>
          <h1>Notice of Principal Executive Office Address Change</h1>
          <p>Effective February 17, 2026, the principal executive office address of
          Palantir Technologies Inc. is 19505 Biscayne Boulevard, Suite 2350,
          Aventura, Florida 33180.</p>
        </body></html>
        """
        notice = MODULE.extract_principal_office_notice(html)
        self.assertEqual(notice["effective_date"], "2026-02-17")
        self.assertEqual(notice["street"], "19505 Biscayne Boulevard, Suite 2350")
        self.assertEqual(notice["city"], "Aventura")
        self.assertEqual(notice["region"], "Florida")
        self.assertEqual(notice["postal"], "33180")
        self.assertEqual(notice["country"], "United States")


if __name__ == "__main__":
    unittest.main()
