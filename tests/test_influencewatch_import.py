from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "import_influencewatch.py"
SPEC = importlib.util.spec_from_file_location("import_influencewatch", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PERSON_HTML = b"""<!doctype html>
<html>
<head>
  <title>Example Person - Influence Watch</title>
  <link rel="canonical" href="https://www.influencewatch.org/person/example-person/">
  <meta name="description" content="Example Person is a public-policy donor.">
  <script type="application/ld+json">
  {"@type":"Article","datePublished":"2026-01-02","dateModified":"2026-02-03","image":"https://www.influencewatch.org/app/uploads/person.jpg"}
  </script>
</head>
<body>
  <main>
    <h1>Example Person</h1>
    <div>Occupation:</div><div>Donor, Activist</div>
    <p>Example Person is a public-policy donor.</p>
    <a href="/non-profit/example-org/">Example Org</a>
  </main>
</body>
</html>
"""

ORG_HTML = b"""<!doctype html>
<html>
<head>
  <title>Example Org - Influence Watch</title>
  <link rel="canonical" href="https://www.influencewatch.org/non-profit/example-org/">
  <meta name="description" content="Example Org is a nonprofit.">
</head>
<body>
  <main>
    <h1>Example Org</h1>
    <div>Type:</div><div>Non-profit, 501(c)(3)</div>
    <div>Issue Areas:</div><div>Economic Policy, Elections Policy</div>
    <div>Website:</div><div>https://example.org</div>
    <div>Tax ID:</div><div>12-3456789</div>
    <p>Example Org is a nonprofit.</p>
  </main>
</body>
</html>
"""


class InfluenceWatchImportTests(unittest.TestCase):
    def test_network_collection_requires_authorization(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            MODULE.require_network_authorization(authorized=False, environment={})
        self.assertIn("express written consent", str(raised.exception))
        MODULE.require_network_authorization(authorized=True, environment={})
        MODULE.require_network_authorization(authorized=False, environment={MODULE.AUTH_ENV: "1"})

    def test_person_profile_is_normalized(self) -> None:
        profile = MODULE.parse_profile(PERSON_HTML, "https://www.influencewatch.org/person/example-person/")
        self.assertEqual("person", profile.dtype)
        self.assertEqual("Example Person", profile.title)
        self.assertEqual(["Donor", "Activist"], MODULE.profile_data(profile)["occupations"])
        self.assertEqual("https://www.influencewatch.org/non-profit/example-org/", profile.links[0][1])
        document = MODULE.profile_document(profile, site_source_id="starintel:source:test")
        self.assertEqual(MODULE.DATASET, document["dataset"])
        self.assertEqual("person", document["dtype"])
        self.assertEqual("source-recorded", document["verification"]["status"])

    def test_org_profile_extracts_identifiers_and_issue_areas(self) -> None:
        profile = MODULE.parse_profile(ORG_HTML, "https://www.influencewatch.org/non-profit/example-org/")
        document = MODULE.profile_document(profile, site_source_id="starintel:source:test")
        self.assertEqual("org", document["dtype"])
        self.assertEqual("12-3456789", document["data"]["tax_id"])
        self.assertEqual(["Economic Policy", "Elections Policy"], document["data"]["sectors"])
        schemes = {item["scheme"] for item in document["identifiers"]}
        self.assertIn("tax-id", schemes)

    def test_internal_profile_links_resolve_when_target_is_present(self) -> None:
        person = MODULE.parse_profile(PERSON_HTML, "https://www.influencewatch.org/person/example-person/")
        org = MODULE.parse_profile(ORG_HTML, "https://www.influencewatch.org/non-profit/example-org/")
        source = MODULE.site_source_document("2026-07-31T00:00:00Z")
        documents = {
            person.url: MODULE.profile_document(person, site_source_id=source["_id"]),
            org.url: MODULE.profile_document(org, site_source_id=source["_id"]),
        }
        relations = MODULE.relation_documents([person, org], documents, site_source_id=source["_id"])
        self.assertEqual(1, len(relations))
        self.assertEqual("references_profile", relations[0]["data"]["predicate"])
        self.assertEqual(documents[org.url]["_id"], relations[0]["data"]["object"])

    def test_sitemap_index_and_urlset_are_parsed(self) -> None:
        index = b'''<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://www.influencewatch.org/wp-sitemap-posts-person-1.xml</loc></sitemap></sitemapindex>'''
        children, urls = MODULE.parse_sitemap(index, MODULE.DEFAULT_SITEMAP_URL)
        self.assertEqual([], urls)
        self.assertEqual("https://www.influencewatch.org/wp-sitemap-posts-person-1.xml", children[0])

        urlset = b'''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.influencewatch.org/person/example-person/</loc></url><url><loc>https://www.influencewatch.org/about-us/</loc></url></urlset>'''
        children, urls = MODULE.parse_sitemap(urlset, children[0])
        self.assertEqual([], children)
        self.assertEqual(["https://www.influencewatch.org/person/example-person/"], urls)

    def test_manifest_counts_generated_records(self) -> None:
        person = MODULE.parse_profile(PERSON_HTML, "https://www.influencewatch.org/person/example-person/")
        records = MODULE.build_records([person], output=Path("imports/influence-watch-db.jsonl"))
        self.assertEqual("dataset-manifest", records[-1]["dtype"])
        self.assertEqual(MODULE.DATASET, records[-1]["data"]["name"])
        self.assertEqual(len(records) - 1, records[-1]["data"]["record_count"])


if __name__ == "__main__":
    unittest.main()
