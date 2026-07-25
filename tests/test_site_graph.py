from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from starintel_site.model import graph


class SiteGraphTests(unittest.TestCase):
    def test_every_non_relation_document_is_a_node_and_relations_are_edges_only(self) -> None:
        person_id = "starintel:person:example"
        org_id = "starintel:org:example"
        claim_id = "starintel:claim:example"
        relation_id = "starintel:relation:example-works-for"
        documents = [
            {
                "_id": person_id,
                "dtype": "person",
                "title": "Example Person",
                "data": {"full_name": "Example Person"},
            },
            {
                "_id": org_id,
                "dtype": "org",
                "title": "Example Org",
                "data": {"name": "Example Org"},
            },
            {
                "_id": claim_id,
                "dtype": "claim",
                "title": "Example Claim",
                "data": {"claim": "Example claim"},
            },
            {
                "_id": relation_id,
                "dtype": "relation",
                "title": "Example Person works for Example Org",
                "data": {
                    "subject": person_id,
                    "predicate": "works_for",
                    "object": org_id,
                },
            },
        ]

        result = graph(documents)

        self.assertEqual(
            {node["id"] for node in result["nodes"]},
            {person_id, org_id, claim_id},
        )
        self.assertNotIn(relation_id, {node["id"] for node in result["nodes"]})
        self.assertIn(
            {"source": person_id, "target": org_id, "label": "works for"},
            result["edges"],
        )

    def test_relation_document_cannot_be_reintroduced_as_an_endpoint_node(self) -> None:
        org_id = "starintel:org:example"
        first_relation_id = "starintel:relation:first"
        second_relation_id = "starintel:relation:second"
        documents = [
            {
                "_id": org_id,
                "dtype": "org",
                "title": "Example Org",
                "data": {"name": "Example Org"},
            },
            {
                "_id": first_relation_id,
                "dtype": "relation",
                "title": "First relation",
                "data": {
                    "subject": org_id,
                    "predicate": "related_to",
                    "object": org_id,
                },
            },
            {
                "_id": second_relation_id,
                "dtype": "relation",
                "title": "Invalid relation endpoint",
                "data": {
                    "subject": first_relation_id,
                    "predicate": "references",
                    "object": org_id,
                },
            },
        ]

        result = graph(documents)

        self.assertEqual({node["id"] for node in result["nodes"]}, {org_id})
        self.assertFalse(any(edge["source"] == first_relation_id for edge in result["edges"]))


if __name__ == "__main__":
    unittest.main()
