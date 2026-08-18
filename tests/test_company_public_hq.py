from __future__ import annotations

import unittest

from scripts.company_public_hq import extract_hq_locality, extract_public_contact_address


class CompanyPublicHqTests(unittest.TestCase):
    def test_extracts_explicit_hq_locality_without_inventing_street(self) -> None:
        raw = """
        <section>
          Located in sunny Costa Mesa, California, Anduril HQ features robust
          facilities for software and hardware engineering.
        </section>
        """

        result = extract_hq_locality(raw)

        self.assertEqual(
            result,
            {
                "city": "Costa Mesa",
                "region": "California",
                "country": "United States",
                "location_type": "headquarters_locality",
                "source_semantics": "explicit headquarters locality",
            },
        )
        self.assertNotIn("street", result)
        self.assertNotIn("postal", result)

    def test_extracts_explicit_public_contact_address_separately(self) -> None:
        raw = """
        Contact information
        Legal Department
        Address: 1400 Anduril, Costa Mesa, CA 92626
        Phone: (949) 891-1607
        """

        result = extract_public_contact_address(raw)

        self.assertEqual(result["street"], "1400 Anduril")
        self.assertEqual(result["city"], "Costa Mesa")
        self.assertEqual(result["region"], "California")
        self.assertEqual(result["postal"], "92626")
        self.assertEqual(result["country"], "United States")
        self.assertEqual(result["location_type"], "public_legal_contact_address")
        self.assertEqual(result["source_semantics"], "explicit public contact address")

    def test_extracts_jobsohio_contact_footer_without_promoting_it_to_hq(self) -> None:
        raw = """
        <footer>
          <h2>ready to make great happen?</h2>
          <p>Let's talk business</p>
          <p>41 S High St #1500<br>Columbus, OH 43215</p>
          <p>(614) 224-6446</p>
        </footer>
        """

        result = extract_public_contact_address(raw)

        self.assertEqual(result["street"], "41 S High St #1500")
        self.assertEqual(result["city"], "Columbus")
        self.assertEqual(result["region"], "Ohio")
        self.assertEqual(result["postal"], "43215")
        self.assertEqual(result["location_type"], "public_organizational_contact_address")
        self.assertEqual(result["source_semantics"], "explicit public organizational contact address")
        with self.assertRaises(ValueError):
            extract_hq_locality(raw)

    def test_extracts_public_agency_footer_address_without_promoting_it_to_hq(self) -> None:
        raw = """
        <footer>
          The Ohio Department of Development • 77 South High Street • 29th Floor •
          Columbus, Ohio 43215 • 614-466-2609
        </footer>
        """

        result = extract_public_contact_address(raw)

        self.assertEqual(result["street"], "77 South High Street, 29th Floor")
        self.assertEqual(result["city"], "Columbus")
        self.assertEqual(result["region"], "Ohio")
        self.assertEqual(result["postal"], "43215")
        self.assertEqual(result["location_type"], "public_organizational_contact_address")
        self.assertEqual(result["source_semantics"], "explicit public agency footer address")
        with self.assertRaises(ValueError):
            extract_hq_locality(raw)

    def test_contact_address_is_not_promoted_to_hq(self) -> None:
        raw = "Address: 1400 Anduril, Costa Mesa, CA 92626"

        with self.assertRaises(ValueError):
            extract_hq_locality(raw)

    def test_hq_locality_requires_explicit_hq_language(self) -> None:
        raw = "Our California team works from Costa Mesa and Irvine."

        with self.assertRaises(ValueError):
            extract_hq_locality(raw)

    def test_contact_address_requires_explicit_address_marker_or_contact_context(self) -> None:
        raw = "Ship returns to 1400 Anduril, Costa Mesa, CA 92626."

        with self.assertRaises(ValueError):
            extract_public_contact_address(raw)


if __name__ == "__main__":
    unittest.main()
