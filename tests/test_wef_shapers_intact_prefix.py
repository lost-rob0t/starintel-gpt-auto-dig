from __future__ import annotations

import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.store import read_transport


class WefShapersIntactPrefixTests(unittest.TestCase):
    def test_verified_packet_count_types_and_digest(self) -> None:
        packet = (
            ROOT
            / "digs"
            / "wef"
            / "global-shapers-legacy-intact-prefix"
            / "starintel-documents.jsonl.gz.b64.parts"
        )
        payload = read_transport(packet)
        documents = [json.loads(line) for line in payload.splitlines() if line.strip()]
        self.assertEqual(len(documents), 8_209)
        self.assertEqual(
            Counter(document["dtype"] for document in documents),
            Counter({"person": 2_736, "relation": 5_472, "org": 1}),
        )
        canonical = "".join(
            json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for document in documents
        )
        self.assertEqual(
            hashlib.sha256(canonical.encode()).hexdigest(),
            "0589735d353f868c5a97b82e9ad043aee14a8873c36d8318a6ce7572b4f09b17",
        )

    def test_recovery_report_is_explicitly_partial(self) -> None:
        report = json.loads(
            (ROOT / "reports" / "wef-global-shapers-intact-prefix.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "partial-intact-prefix")
        self.assertEqual(report["prefix"]["people"], 2_736)
        self.assertEqual(report["packet"]["documents"], 8_209)
        self.assertEqual(
            report["missing_suffix_status"],
            "requires-live-and-archive-reconstruction",
        )


if __name__ == "__main__":
    unittest.main()
