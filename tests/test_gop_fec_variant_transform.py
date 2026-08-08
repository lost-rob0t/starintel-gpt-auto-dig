#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_gop_fec_variant.py"
SPEC = importlib.util.spec_from_file_location("gop_variant", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GOPFECVariantTransformTest(unittest.TestCase):
    def transformed(self, name: str) -> str:
        text = MODULE.transform(MODULE.SCRIPTS / name)
        compile(text, name, "exec")
        return text

    def test_every_allowed_importer_is_gop_scoped_and_schema_adapted(self) -> None:
        for name in sorted(MODULE.ALLOWED):
            with self.subTest(name=name):
                text = self.transformed(name)
                self.assertIn('DATASET = "gop"', text)
                self.assertIn(f'GENERATED_AT = "{MODULE.GENERATED_AT}"', text)
                self.assertIn('fec_legacy_data', text)
                self.assertIn('_gop_document_schema', text)
                self.assertNotIn('DATASET = "dnc"', text)
                self.assertNotIn('starintel:org:dnc', text)
                self.assertNotIn('C00010603', text)
                self.assertNotIn('PARTY_CODES = {"DEM", "DFL"}', text)
                self.assertNotIn('DEM|DFL', text)
                self.assertNotIn('DEM and DFL', text)
                self.assertNotIn('DEM or DFL', text)
                self.assertNotIn('DFL', text)

    def test_committee_dfl_priority_bonus_is_removed(self) -> None:
        text = self.transformed("import_dnc_fec_democratic_committees.py")
        self.assertIn('PARTY_CODES = {"REP"}', text)
        self.assertNotIn('if party_code == "REP":\n        base += 0.01', text)
        self.assertIn('"scheme": "party_code_set", "value": "REP"', text)

    def test_administrative_fine_current_headers_are_normalized(self) -> None:
        text = self.transformed("import_dnc_fec_administrative_fines.py")
        self.assertIn('REPUBLICAN(?:S)?|GOP|RNC', text)
        self.assertNotIn('DEMOCRAT(?:IC|S)?', text)
        self.assertIn('GOP_CLASSIFICATION_BASIS', text)
        self.assertIn('"case_number": "CAS_NUM"', text)
        self.assertIn('ADMIN_FINE_FIELD_ALIASES.get(name, name)', text)

    def test_current_candidate_linkages_can_reference_retired_committees(self) -> None:
        text = self.transformed("import_dnc_fec_democratic_candidates.py")
        self.assertIn('unresolved_linked_committee_ids', text)
        self.assertIn('linkages = [row for row in linkages if row["CMTE_ID"].strip() not in missing_set]', text)
        self.assertNotIn('raise RuntimeError(f"candidate-linked committees missing from committee master:', text)

    def test_independent_expenditure_current_headers_and_party_name_are_normalized(self) -> None:
        text = self.transformed("import_dnc_fec_independent_expenditures.py")
        self.assertIn('\nimport io\n', text)
        self.assertIn('"cand_id": "CAN_ID"', text)
        self.assertIn('"cand_pty_aff": "CAN_PAR_AFF"', text)
        self.assertIn('"amndt_ind": "AMN_IND"', text)
        self.assertIn('"receipt_dat": "REC_DT"', text)
        self.assertIn('IE_FIELD_ALIASES.get(name, name)', text)
        self.assertIn('reported_party != "REPUBLICAN PARTY"', text)

    def test_rnc_operating_expenditure_scope(self) -> None:
        text = self.transformed("import_dnc_fec_oppexp.py")
        self.assertIn('COMMITTEE_ID = "C00003418"', text)
        self.assertIn('DATASET = "gop"', text)


if __name__ == "__main__":
    unittest.main()
