from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starintel_doc.linking import (
    AmbiguousRecordError,
    create_relation_document,
    relation_neighbors,
    resolve_record,
    search_records,
)
from starintel_doc.model import Document
from starintel_doc.store import compact


class LinkingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "db" / "person").mkdir(parents=True)
        (self.root / "db" / "org").mkdir(parents=True)
        (self.root / "db" / "relation").mkdir(parents=True)
        (self.root / "digs" / "wef" / "packet").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_db(self, document: dict) -> None:
        target = self.root / "db" / document["dtype"] / f"{document['_id']}.ndjson"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(compact(document) + "\n", encoding="utf-8")

    def make_person(self, doc_id: str, title: str, aliases: list[str] | None = None) -> dict:
        return Document.create(
            "person",
            "wef",
            doc_id=doc_id,
            title=title,
            aliases=aliases or [],
            data={"name": title, "full_name": title},
        ).to_dict()

    def make_org(self, doc_id: str, title: str) -> dict:
        return Document.create(
            "org",
            "wef",
            doc_id=doc_id,
            title=title,
            data={"name": title},
        ).to_dict()

    def test_search_prefers_db_copy_and_resolves_alias(self) -> None:
        fink = self.make_person(
            "starintel:person:laurence-d-fink",
            "Laurence D. Fink",
            ["Larry Fink"],
        )
        self.write_db(fink)
        packet = dict(fink)
        packet["version"] = 99
        packet_path = self.root / "digs" / "wef" / "packet" / "starintel-documents.jsonl"
        packet_path.write_text(compact(packet) + "\n", encoding="utf-8")

        matches = search_records(self.root, "Larry Fink")
        self.assertEqual(matches[0].document["_id"], fink["_id"])
        self.assertEqual(matches[0].located.surface, "db")

        resolved = resolve_record(self.root, "Larry Fink")
        self.assertEqual(resolved.document["_id"], fink["_id"])

    def test_resolve_rejects_ambiguous_exact_labels(self) -> None:
        self.write_db(self.make_person("starintel:person:alex-one", "Alex Smith"))
        self.write_db(self.make_person("starintel:person:alex-two", "Alex Smith"))
        with self.assertRaises(AmbiguousRecordError):
            resolve_record(self.root, "Alex Smith")

    def test_create_relation_uses_canonical_ids(self) -> None:
        fink = self.make_person(
            "starintel:person:laurence-d-fink",
            "Laurence D. Fink",
            ["Larry Fink"],
        )
        wef = self.make_org(
            "starintel:org:world-economic-forum",
            "World Economic Forum",
        )
        self.write_db(fink)
        self.write_db(wef)

        relation = create_relation_document(
            self.root,
            dataset="wef",
            subject_query="Larry Fink",
            predicate="co_chairs",
            object_query="World Economic Forum",
            confidence=0.99,
        )
        self.assertEqual(relation["dtype"], "relation")
        self.assertEqual(relation["data"]["subject"], fink["_id"])
        self.assertEqual(relation["data"]["object"], wef["_id"])
        self.assertEqual(relation["data"]["predicate"], "co_chairs")

    def test_neighbors_returns_inbound_and_outbound_relations(self) -> None:
        fink = self.make_person(
            "starintel:person:laurence-d-fink",
            "Laurence D. Fink",
            ["Larry Fink"],
        )
        wef = self.make_org(
            "starintel:org:world-economic-forum",
            "World Economic Forum",
        )
        blackrock = self.make_org("starintel:org:blackrock", "BlackRock")
        for document in (fink, wef, blackrock):
            self.write_db(document)

        relation_a = create_relation_document(
            self.root,
            dataset="wef",
            subject_query="Larry Fink",
            predicate="co_chairs",
            object_query="World Economic Forum",
        )
        relation_b = create_relation_document(
            self.root,
            dataset="wef",
            subject_query="BlackRock",
            predicate="led_by",
            object_query="Larry Fink",
        )
        self.write_db(relation_a)
        self.write_db(relation_b)

        resolved, relations = relation_neighbors(self.root, "Larry Fink")
        self.assertEqual(resolved.document["_id"], fink["_id"])
        self.assertEqual(
            {item.document["_id"] for item in relations},
            {relation_a["_id"], relation_b["_id"]},
        )


if __name__ == "__main__":
    unittest.main()
