#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from starintel_doc.validation import validate_document

PACKET = Path("digs/fed/2026-07-31-brett-leatherman-adverse-depth-1/starintel-documents.jsonl")
LEGAL_ID = "starintel:legal:lacroix-v-leatherman-25-cv-13452"
PERSON_ID = "starintel:person:brett-leatherman"


def main() -> None:
    documents = [json.loads(line) for line in PACKET.read_text(encoding="utf-8").splitlines() if line.strip()]
    repaired = False

    for document in documents:
        if document.get("_id") != LEGAL_ID:
            validate_document(document)
            continue

        original_data = document.get("data", {})
        document["dtype"] = "claim"
        document["data"] = {
            "claim": (
                "Lacroix v. Leatherman, No. 25-cv-13452, is a pending federal civil action "
                "alleging surveillance, harassment, abuse of investigative authority, and evidence "
                "misconduct by Brett Leatherman and other FBI officials; no merits finding "
                "substantiating those allegations was identified in the reviewed record."
            ),
            "subject_ids": [PERSON_ID],
            "claim_type": "pending_litigation_allegation",
            "polarity": "adverse_allegation",
            "certainty": 0.99,
            "status": "pending-unadjudicated-allegation",
        }
        document.setdefault("extensions", {})["legal_case"] = original_data
        document["verification"] = {
            "status": "lawsuit-existence-verified-allegations-unverified",
            "verified": False,
            "methods": ["docket URL reconciliation", "plaintiff-source classification"],
            "last_reviewed_at": "2026-07-31T06:25:00Z",
        }
        document.setdefault("assessment", {})["caveats"] = [
            "The existence of the lawsuit is documented; its allegations are not findings.",
            "The plaintiff controls the principal narrative sources reviewed.",
            "No court order substantiating misconduct by Leatherman was identified in this pass.",
        ]
        validate_document(document)
        repaired = True

    if not repaired:
        raise SystemExit(f"missing expected document: {LEGAL_ID}")

    PACKET.write_text(
        "\n".join(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            for document in documents
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"validated_documents={len(documents)} repaired={LEGAL_ID}")


if __name__ == "__main__":
    main()
