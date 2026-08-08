#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import_gop_fec_deidentified_receipts.py"
SPEC = importlib.util.spec_from_file_location("gop_receipts", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GOPFECDeidentifiedReceiptsTest(unittest.TestCase):
    def test_duplicate_rows_are_deduped_and_identity_is_not_emitted(self) -> None:
        values = {
            "CMTE_ID": MODULE.COMMITTEE_ID,
            "AMNDT_IND": "N",
            "RPT_TP": "M6",
            "TRANSACTION_PGI": "P2026",
            "IMAGE_NUM": "202608080000000001",
            "TRANSACTION_TP": "15E",
            "ENTITY_TP": "IND",
            "NAME": "PRIVATE PERSON SHOULD NEVER APPEAR",
            "CITY": "PRIVATECITY",
            "STATE": "OH",
            "ZIP_CODE": "43000",
            "EMPLOYER": "PRIVATE EMPLOYER",
            "OCCUPATION": "PRIVATE OCCUPATION",
            "TRANSACTION_DT": "08082026",
            "TRANSACTION_AMT": "125.50",
            "OTHER_ID": "",
            "TRAN_ID": "T-TEST-1",
            "FILE_NUM": "9999999",
            "MEMO_CD": "",
            "MEMO_TEXT": "PRIVATE MEMO SHOULD NEVER APPEAR",
            "SUB_ID": "9999999999999999999",
        }
        line = "|".join(values[field] for field in MODULE.FIELDS) + "|\n"

        with tempfile.TemporaryDirectory(prefix="gop-receipt-test-") as tmp:
            root = Path(tmp)
            archive_path = root / "indiv26.zip"
            output = root / "output"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("by_date/part.txt", line)
                archive.writestr("itcont.txt", line)

            manifest = MODULE.generate(
                archive_path,
                output,
                2026,
                MODULE.COMMITTEE_ID,
                "2026-08-08T21:50:00Z",
            )

            self.assertEqual(manifest["raw_matching_rows"], 2)
            self.assertEqual(manifest["duplicate_sub_id_rows"], 1)
            self.assertEqual(manifest["unique_fec_sub_ids"], 1)
            self.assertEqual(manifest["total_documents"], 2)

            base = output / "starintel-documents.jsonl.gz.b64"
            part_names = [
                line.strip()
                for line in (output / "starintel-documents.jsonl.gz.b64.parts")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            encoded = "".join((output / name).read_text(encoding="utf-8").strip() for name in part_names)
            payload = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
            docs = [json.loads(line) for line in payload.splitlines() if line.strip()]

            finance = next(doc for doc in docs if doc["dtype"] == "campaign-finance")
            self.assertNotIn("donor_id", finance["data"])
            self.assertNotIn("entity_id", finance["data"])
            self.assertEqual(finance["data"]["recipient_id"], MODULE.RNC_ID)
            self.assertFalse(finance["handling"]["pii"])

            forbidden = (
                values["NAME"],
                values["CITY"],
                values["STATE"],
                values["ZIP_CODE"],
                values["EMPLOYER"],
                values["OCCUPATION"],
                values["MEMO_TEXT"],
            )
            for value in forbidden:
                self.assertNotIn(value, payload)

            self.assertTrue(base.parent.is_dir())


if __name__ == "__main__":
    unittest.main()
