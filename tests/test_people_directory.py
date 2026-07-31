from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from starintel_doc.model import Document
from starintel_site.people import build_people_directory


class PeopleDirectoryTests(unittest.TestCase):
    def test_generates_alumni_profile_and_filters(self) -> None:
        person_id = "starintel:person:jane-doe"
        org_id = "starintel:org:example-fellowship"
        person = Document.create(
            "person",
            "example-alumni",
            doc_id=person_id,
            title="Jane Doe",
            summary="Researcher and 2024 fellowship alumna.",
            data={
                "full_name": "Jane Doe",
                "bio": "Researcher and 2024 fellowship alumna.",
                "public_roles": ["Researcher"],
            },
            sources=[{"url": "https://example.org/alumni/jane-doe", "title": "Jane Doe profile"}],
        ).to_dict()
        organization = Document.create(
            "org",
            "example-alumni",
            doc_id=org_id,
            title="Example Fellowship",
            summary="A public fellowship program.",
            data={"name": "Example Fellowship", "org_type": "fellowship"},
            sources=[{"url": "https://example.org/alumni", "title": "Alumni directory"}],
        ).to_dict()
        relation = Document.create(
            "relation",
            "example-alumni",
            doc_id="starintel:relation:jane-doe-alumnus-of-example-fellowship",
            title="Jane Doe alumnus of Example Fellowship",
            summary="Official alumni roster records Jane Doe in the 2024 cohort.",
            data={
                "subject": person_id,
                "predicate": "alumnus_of",
                "object": org_id,
                "directed": True,
                "qualifiers": {"cohort": "2024", "program": "Public Leadership Fellowship", "role": "Fellow"},
                "confidence": 0.99,
            },
            sources=[{"url": "https://example.org/alumni/2024", "title": "2024 alumni cohort"}],
        ).to_dict()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_root = root / "input"
            packet = input_root / "example" / "run" / "starintel-documents.jsonl"
            packet.parent.mkdir(parents=True)
            packet.write_text(
                "".join(json.dumps(document, separators=(",", ":"), sort_keys=True) + "\n" for document in (person, organization, relation)),
                encoding="utf-8",
            )
            output = root / "site"
            output.mkdir()
            (output / "index.html").write_text(
                '<html><body><header><nav><a href="index.html">Research</a></nav></header><section class="stats dashboard-stats"></section></body></html>',
                encoding="utf-8",
            )
            assets = root / "assets"
            assets.mkdir()
            (assets / "people.css").write_text(".people-grid{}", encoding="utf-8")
            (assets / "people.js").write_text("(() => {})();", encoding="utf-8")

            result = build_people_directory(input_root, output, assets)

            self.assertEqual(result["people"], 1)
            self.assertEqual(result["alumni"], 1)
            directory_index = (output / "people" / "index.html").read_text(encoding="utf-8")
            profile = (output / "people" / "person-jane-doe.html").read_text(encoding="utf-8")
            records = json.loads((output / "people" / "people.json").read_text(encoding="utf-8"))
            root_index = (output / "index.html").read_text(encoding="utf-8")

            self.assertIn("People directory", directory_index)
            self.assertIn("Jane Doe", directory_index)
            self.assertIn("Membership and alumni history", profile)
            self.assertIn("Public Leadership Fellowship", profile)
            self.assertIn("2024", profile)
            self.assertEqual(records[0]["memberships"][0]["status"], "alumni")
            self.assertEqual(records[0]["memberships"][0]["cohort"], "2024")
            self.assertIn('href="people/index.html"', root_index)


if __name__ == "__main__":
    unittest.main()
