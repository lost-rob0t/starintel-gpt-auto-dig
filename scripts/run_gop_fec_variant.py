#!/usr/bin/env python3
from __future__ import annotations

import argparse
import runpy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
GENERATED_AT = "2026-08-08T21:55:00Z"

ALLOWED = {
    "import_dnc_fec_administrative_fines.py",
    "import_dnc_fec_committee_transactions.py",
    "import_dnc_fec_democratic_candidates.py",
    "import_dnc_fec_democratic_committees.py",
    "import_dnc_fec_independent_expenditures.py",
    "import_dnc_fec_oppexp.py",
}

REPLACEMENTS = (
    ('2026-07-31', '2026-08-08'),
    ('NAME_LEAD_RE = re.compile(r"\\b(?:DEMOCRAT(?:IC|S)?|DFL|DNC)\\b", re.IGNORECASE)',
     'NAME_LEAD_RE = re.compile(r"\\b(?:REPUBLICAN(?:S)?|GOP|RNC)\\b", re.IGNORECASE)'),
    ('    if party_code == "DFL":\n        base += 0.01\n', ''),
    ('PARTY_CODES = {"DEM", "DFL"}', 'PARTY_CODES = {"REP"}'),
    ('DEM|DFL', 'REP'),
    ('`DEM` or `DFL`', '`REP`'),
    ('DEM and DFL', 'REP'),
    ('DEM or DFL', 'REP'),
    ('DEM/DFL', 'REP'),
    ('MAX_MATCHING_ROWS = 50_000', 'MAX_MATCHING_ROWS = 250_000'),
    ('C00010603', 'C00003418'),
    ('starintel:org:dnc', 'starintel:org:republican-national-committee'),
    ('democratic-party-fec-affiliation', 'republican-party-fec-affiliation'),
    ('DEMOCRATIC_PARTY_ID', 'REPUBLICAN_PARTY_ID'),
    ('"DEM"', '"REP"'),
    ("'DEM'", "'REP'"),
    ('DFL', 'REP'),
    ('DEMOCRATIC', 'REPUBLICAN'),
    ('Democratic', 'Republican'),
    ('democratic', 'republican'),
    ('DEMOCRAT', 'REPUBLICAN'),
    ('Democrat', 'Republican'),
    ('democrat', 'republican'),
    ('DNC', 'GOP'),
    ('dnc', 'gop'),
)

VALIDATION_IMPORT = "from starintel_doc.validation import validate_document"
VALIDATION_COMPAT = '''from starintel_doc.schema_org import document_schema as _gop_document_schema
from starintel_doc.validation import validate_document as _gop_schema_validate_document


def validate_document(document: dict[str, Any]) -> None:
    data = document.get("data")
    dtype = str(document.get("dtype") or "").strip().lower().replace("_", "-")
    if isinstance(data, dict) and dtype:
        schema = _gop_document_schema(dtype)
        data_schema = schema.get("properties", {}).get("data", {})
        allowed = set(data_schema.get("properties", {}))
        if allowed:
            extras = {key: data.pop(key) for key in list(data) if key not in allowed}
            if extras:
                extensions = document.setdefault("extensions", {})
                legacy = extensions.setdefault("fec_legacy_data", {})
                legacy.update(extras)
    _gop_schema_validate_document(document)
'''

ADMIN_FINE_ALIASES = '''ADMIN_FINE_FIELD_ALIASES = {
    "case_number": "CAS_NUM",
    "cmte_id": "COM_ID",
    "cmte_name": "COM_NAM",
    "report_type": "REP_TYP",
    "report_year": "REP_YEA",
    "fine_amount": "FIN_AMO",
    "office": "OFF",
    "state": "STA",
    "district": "DIS",
    "cand_name": "CAN_NAM",
    "late_filed_not_filed": "LAT_FIL_NOT_FIL",
    "paid_yes_no": "PAI_YES_NO",
}
'''

IE_FIELD_ALIASES = '''IE_FIELD_ALIASES = {
    "cand_id": "CAN_ID",
    "cand_name": "CAN_NAM",
    "spe_id": "SPE_ID",
    "spe_nam": "SPE_NAM",
    "ele_type": "ELE_TYP",
    "can_office_state": "CAN_OFF_STA",
    "can_office_dis": "CAN_OFF_DIS",
    "can_office": "CAN_OFF",
    "cand_pty_aff": "CAN_PAR_AFF",
    "exp_amo": "EXP_AMO",
    "exp_date": "EXP_DAT",
    "agg_amo": "AGG_AMO",
    "sup_opp": "SUP_OPP",
    "pur": "PUR",
    "pay": "PAY",
    "file_num": "FILE_NUM",
    "amndt_ind": "AMN_IND",
    "tran_id": "TRA_ID",
    "image_num": "IMA_NUM",
    "receipt_dat": "REC_DT",
    "fec_election_yr": "FEC_ELECTION_YR",
    "prev_file_num": "PREV_FILE_NUM",
    "dissem_dt": "DISSEM_DT",
}
'''


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Run an allow-listed DNC FEC importer as a deterministic GOP/RNC variant"
    )
    parser.add_argument("source", help="DNC FEC importer filename under scripts/")
    return parser.parse_known_args()


def transformed_script_name(source_name: str) -> str:
    name = source_name.replace("dnc", "gop")
    return name.replace("democratic", "republican")


def normalize_generated_at(text: str) -> str:
    lines = text.splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith("GENERATED_AT = "):
            lines[index] = f'GENERATED_AT = "{GENERATED_AT}"'
            replaced = True
    if not replaced:
        raise RuntimeError("source importer no longer declares GENERATED_AT")
    return "\n".join(lines) + "\n"


def install_validation_compat(text: str) -> str:
    if VALIDATION_IMPORT not in text:
        raise RuntimeError("source importer no longer imports validate_document in the expected form")
    return text.replace(VALIDATION_IMPORT, VALIDATION_COMPAT, 1)


def install_missing_imports(text: str) -> str:
    if "io." in text and "\nimport io\n" not in text:
        anchor = "import hashlib\n"
        if anchor not in text:
            raise RuntimeError("cannot install missing io import")
        text = text.replace(anchor, anchor + "import io\n", 1)
    return text


def install_candidate_linkage_compat(text: str, source_name: str) -> str:
    if source_name != "import_dnc_fec_democratic_candidates.py":
        return text
    old = '''        missing = sorted(linked_committee_ids - committee_rows.keys())
        if missing:
            raise RuntimeError(f"candidate-linked committees missing from committee master: {missing[:20]}")
'''
    new = '''        missing = sorted(linked_committee_ids - committee_rows.keys())
        if missing:
            missing_set = set(missing)
            linkages = [row for row in linkages if row["CMTE_ID"].strip() not in missing_set]
'''
    if old not in text:
        raise RuntimeError("candidate missing-committee guard changed; review GOP compatibility")
    text = text.replace(old, new, 1)
    metadata_anchor = '''            "raw_counts": {"candidate_rows": len(all_candidates), "committee_rows": len(all_committees), "linkage_rows": len(all_linkages)},
'''
    if metadata_anchor in text:
        text = text.replace(
            metadata_anchor,
            metadata_anchor + '            "unresolved_linked_committee_ids": missing,\n',
            1,
        )
    return text


def install_admin_fine_header_compat(text: str, source_name: str) -> str:
    if source_name != "import_dnc_fec_administrative_fines.py":
        return text
    required_anchor = "REQUIRED_FIELDS = {"
    if required_anchor not in text:
        raise RuntimeError("administrative-fine field declaration changed")
    text = text.replace(required_anchor, ADMIN_FINE_ALIASES + "\n" + required_anchor, 1)
    old = '''        reader = csv.DictReader(handle)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(f"administrative-fine CSV lacks fields: {sorted(missing)}")
        for row in reader:
'''
    new = '''        reader = csv.DictReader(handle)
        normalized_fields = {ADMIN_FINE_FIELD_ALIASES.get(name, name) for name in (reader.fieldnames or [])}
        missing = REQUIRED_FIELDS - normalized_fields
        if missing:
            raise RuntimeError(f"administrative-fine CSV lacks fields: {sorted(missing)}")
        for raw_row in reader:
            row = {ADMIN_FINE_FIELD_ALIASES.get(key, key): value for key, value in raw_row.items()}
'''
    if old not in text:
        raise RuntimeError("administrative-fine CSV reader changed; review GOP compatibility")
    return text.replace(old, new, 1)


def install_independent_expenditure_header_compat(text: str, source_name: str) -> str:
    if source_name != "import_dnc_fec_independent_expenditures.py":
        return text
    required_anchor = "REQUIRED_IE_FIELDS = {"
    if required_anchor not in text:
        raise RuntimeError("independent-expenditure field declaration changed")
    text = text.replace(required_anchor, IE_FIELD_ALIASES + "\n" + required_anchor, 1)
    old = '''        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED_IE_FIELDS - fields
        if missing:
            raise RuntimeError(f"independent-expenditure CSV lacks fields: {sorted(missing)}")
        fieldnames = list(reader.fieldnames or [])
        with filtered_path.open("wb") as raw_out, gzip.GzipFile(filename="", mode="wb", fileobj=raw_out, compresslevel=9, mtime=0) as compressed:
            buffer = io.StringIO()
            csv_writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\\n")
'''
    new = '''        reader = csv.DictReader(handle)
        fieldnames = [IE_FIELD_ALIASES.get(name, name) for name in (reader.fieldnames or [])]
        missing = REQUIRED_IE_FIELDS - set(fieldnames)
        if missing:
            raise RuntimeError(f"independent-expenditure CSV lacks fields: {sorted(missing)}")
        with filtered_path.open("wb") as raw_out, gzip.GzipFile(filename="", mode="wb", fileobj=raw_out, compresslevel=9, mtime=0) as compressed:
            buffer = io.StringIO()
            csv_writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\\n")
'''
    if old not in text:
        raise RuntimeError("independent-expenditure CSV reader changed; review GOP compatibility")
    text = text.replace(old, new, 1)
    old_row = '''                row = {key: (value or "") for key, value in raw_row.items() if key is not None}
                fec_candidate_id = row["CAN_ID"].strip()
                reported_party = row["CAN_PAR_AFF"].strip().upper()
                if fec_candidate_id not in republican_candidate_ids and reported_party not in PARTY_CODES:
'''
    new_row = '''                row = {IE_FIELD_ALIASES.get(key, key): (value or "") for key, value in raw_row.items() if key is not None}
                fec_candidate_id = row["CAN_ID"].strip()
                reported_party = row["CAN_PAR_AFF"].strip().upper()
                if fec_candidate_id not in republican_candidate_ids and reported_party not in PARTY_CODES and reported_party != "REPUBLICAN PARTY":
'''
    if old_row not in text:
        raise RuntimeError("independent-expenditure row normalization changed; review GOP compatibility")
    return text.replace(old_row, new_row, 1)


def transform(source_path: Path) -> str:
    text = source_path.read_text(encoding="utf-8")
    if 'DATASET = "dnc"' not in text:
        raise RuntimeError(f"{source_path.name} is no longer a DNC importer; review adapter")

    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    text = normalize_generated_at(text)
    text = install_missing_imports(text)
    text = install_candidate_linkage_compat(text, source_path.name)
    text = install_admin_fine_header_compat(text, source_path.name)
    text = install_independent_expenditure_header_compat(text, source_path.name)
    text = install_validation_compat(text)

    generated_name = transformed_script_name(source_path.name)
    text = text.replace(
        f"python3 scripts/{generated_name}",
        f"python3 scripts/run_gop_fec_variant.py {source_path.name}",
    )

    required = (
        'DATASET = "gop"',
        f'GENERATED_AT = "{GENERATED_AT}"',
        'StarIntel-AutoDig/0.9',
        'fec_legacy_data',
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError(f"GOP transform missing required markers: {missing}")

    forbidden = (
        'DATASET = "dnc"',
        'starintel:org:dnc',
        'PARTY_CODES = {"DEM", "DFL"}',
        'C00010603',
        'DEM|DFL',
        'DEM and DFL',
        'DEM or DFL',
        'DFL',
        'DEMOCRAT(?:IC|S)?',
    )
    leaked = [marker for marker in forbidden if marker in text]
    if leaked:
        raise RuntimeError(f"GOP transform retained DNC-specific markers: {leaked}")

    if "PARTY_CODES" in text and 'PARTY_CODES = {"REP"}' not in text:
        raise RuntimeError("party-filtering importer did not resolve to REP-only")
    if source_path.name == "import_dnc_fec_oppexp.py" and 'COMMITTEE_ID = "C00003418"' not in text:
        raise RuntimeError("RNC-scoped importer did not resolve to C00003418")
    if source_path.name == "import_dnc_fec_administrative_fines.py":
        if 'REPUBLICAN(?:S)?|GOP|RNC' not in text:
            raise RuntimeError("administrative-fine GOP name-lead matcher was not installed")
        if '"case_number": "CAS_NUM"' not in text:
            raise RuntimeError("current administrative-fine header aliases were not installed")
    if source_path.name == "import_dnc_fec_democratic_candidates.py" and "unresolved_linked_committee_ids" not in text:
        raise RuntimeError("candidate missing-committee compatibility was not installed")
    if source_path.name == "import_dnc_fec_independent_expenditures.py":
        if '"cand_id": "CAN_ID"' not in text:
            raise RuntimeError("current independent-expenditure header aliases were not installed")
        if 'reported_party != "REPUBLICAN PARTY"' not in text:
            raise RuntimeError("current independent-expenditure party-name compatibility was not installed")

    return text


def main() -> int:
    ns, forwarded = parse_args()
    source_path = SCRIPTS / Path(ns.source).name
    if source_path.name == "import_dnc_fec_individual_contributions.py":
        raise RuntimeError(
            "identity-bearing individual-contribution import is disabled for GOP; "
            "use scripts/import_gop_fec_deidentified_receipts.py"
        )
    if source_path.name not in ALLOWED:
        raise RuntimeError(f"unsupported GOP variant source: {source_path.name}")
    if not source_path.is_file():
        raise RuntimeError(f"missing source importer: {source_path}")

    transformed = transform(source_path)
    old_argv = sys.argv[:]
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".py",
            prefix=".gop-variant-",
            dir=SCRIPTS,
            delete=False,
        ) as handle:
            handle.write(transformed)
            temp_path = Path(handle.name)

        sys.argv = [str(temp_path), *forwarded]
        runpy.run_path(str(temp_path), run_name="__main__")
    finally:
        sys.argv = old_argv
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
