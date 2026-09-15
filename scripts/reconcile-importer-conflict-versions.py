#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATES: dict[str, dict[str, int]] = {
    "digs/anarchist-violence/2026-09-08-area-codes-a-234-267/starintel-documents.jsonl": {
        "starintel:org:wooden-shoe-books": 2,
    },
    "digs/anarchist-violence/2026-09-08-canton-fnb-expansion/starintel-documents.jsonl": {
        "starintel:org:canton-food-not-bombs": 2,
    },
    "digs/anarchist-violence/2026-09-09-election-comms-consulting-media-pass-12/starintel-documents.jsonl": {
        "starintel:source:targeted-victory-home-2026-09-09": 2,
        "starintel:org:targeted-victory": 2,
        "starintel:org:majority-strategies": 2,
        "starintel:person:zac-moffatt": 2,
    },
    "digs/anarchist-violence/2026-09-10-axiom-republican-consulting-network-pass-35/starintel-documents.jsonl": {
        "starintel:org:axiom-strategies": 2,
        "starintel:org:axmedia": 2,
        "starintel:person:jeff-roe": 2,
        "starintel:relation:jeff-roe-executive-axiom": 2,
    },
    "digs/anarchist-violence/2026-09-10-election-admin-vendor-comms-pass-31/starintel-documents.jsonl": {"starintel:org:democracy-live": 2},
    "digs/anarchist-violence/2026-09-10-election-comms-legal-information-pass-16/starintel-documents.jsonl": {"starintel:org:protect-democracy": 2},
    "digs/anarchist-violence/2026-09-10-election-comms-mobilization-infrastructure-pass-22/starintel-documents.jsonl": {
        "starintel:org:bonterra": 2,
        "starintel:org:mobilize": 2,
        "starintel:org:catalist": 2,
        "starintel:org:ballotready": 2,
    },
    "digs/anarchist-violence/2026-09-10-election-comms-voter-data-infrastructure-pass-24/starintel-documents.jsonl": {
        "starintel:org:targetsmart": 2,
        "starintel:org:victory-waves": 2,
        "starintel:org:ngp-van": 2,
    },
    "digs/anarchist-violence/2026-09-10-election-comms-ngp-van-pass-36/starintel-documents.jsonl": {"starintel:org:ngp-van": 3},
    "digs/anarchist-violence/2026-09-10-election-protection-coalition-pass-29/starintel-documents.jsonl": {"starintel:org:naacp": 2},
    "digs/anarchist-violence/2026-09-10-election-results-media-distribution-pass-32/starintel-documents.jsonl": {
        "starintel:org:associated-press": 2,
        "starintel:org:abc-news": 2,
        "starintel:org:cbs-news": 2,
        "starintel:org:cnn": 2,
        "starintel:org:nbc-news": 2,
        "starintel:org:fox-news-media": 2,
        "starintel:org:edison-research": 2,
        "starintel:person:joe-lenski": 2,
    },
    "digs/anarchist-violence/2026-09-10-election-texting-compliance-pass-19/starintel-documents.jsonl": {"starintel:org:rumbleup": 2},
    "digs/anarchist-violence/2026-09-10-political-messaging-verification-pass-34/starintel-documents.jsonl": {
        "starintel:org:campaign-verify": 2,
        "starintel:org:twilio": 2,
        "starintel:org:ctia": 2,
        "starintel:relation:campaign-verify-vetting-partner-tcr": 2,
    },
    "digs/fed/2026-08-19-national-security-adviser-eop-location/starintel-documents.jsonl": {"starintel:person:marco-rubio": 2},
    "digs/palantir/2026-07-25-vance-thiel-executive-branch/starintel-documents.jsonl": {
        "starintel:person:jd-vance": 2,
        "starintel:relation:michael-kratsios-formerly-employed-thiel-capital": 2,
    },
    "digs/palantir/2026-07-25-related-orgs-access/starintel-documents.jsonl": {
        "starintel:org:narya-capital": 2,
        "starintel:relation:jd-vance-cofounded-narya": 2,
        "starintel:org:mithril-capital": 2,
    },
    "digs/wef/2026-07-31-thiel-company-employee-enumeration-depth-1/starintel-documents.jsonl": {"starintel:org:founders-fund": 2},
    "digs/anarchist-violence/2026-09-08-area-codes-b-274-283-301/starintel-documents.jsonl": {
        "starintel:org:frederick-food-not-bombs": 2,
        "starintel:investigation-target:frederick-food-not-bombs-area-code-expansion": 2,
    },
    "digs/anarchist-violence/2026-09-08-ohio-fnb-dayton-athens-expansion/starintel-documents.jsonl": {"starintel:org:food-not-bombs-athens-ohio": 2},
    "digs/anarchist-violence/2026-09-09-area-code-shard-a-pass-14/starintel-documents.jsonl": {
        "starintel:org:urbana-champaign-independent-media-center": 2,
        "starintel:investigation-target:urbana-champaign-independent-media-center-area-code-expansion": 2,
    },
    "digs/anarchist-violence/2026-09-09-area-code-shard-a-pass-16/starintel-documents.jsonl": {
        "starintel:org:cincy-food-not-bombs": 2,
        "starintel:investigation-target:cincy-food-not-bombs-area-code-expansion": 2,
    },
    "digs/anarchist-violence/2026-09-09-area-codes-b-448-463-469/starintel-documents.jsonl": {
        "starintel:org:dfw-support-committee": 2,
        "starintel:investigation-target:dfw-support-committee-area-code-expansion": 2,
        "starintel:org:feed-the-people-dtx-mutual-aid": 2,
        "starintel:investigation-target:feed-the-people-dtx-mutual-aid-area-code-expansion": 2,
    },
    "digs/anarchist-violence/2026-09-09-area-codes-b-661-667-679/starintel-documents.jsonl": {
        "starintel:org:eastside-mutual-aid-detroit": 2,
        "starintel:investigation-target:eastside-mutual-aid-detroit-area-code-expansion": 2,
        "starintel:org:detroit-peer-respite": 2,
        "starintel:investigation-target:detroit-peer-respite-area-code-expansion": 2,
    },
}


def rewrite(path: Path, wanted: dict[str, int]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        doc = json.loads(line)
        doc_id = doc.get("_id")
        if doc_id in wanted:
            if doc.get("version") != 1:
                raise RuntimeError(f"{path.relative_to(ROOT)}: {doc_id} expected version 1, got {doc.get('version')!r}")
            doc["version"] = wanted[doc_id]
            seen.add(doc_id)
            line = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
        out.append(line)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"{path.relative_to(ROOT)} missing IDs: {sorted(missing)}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    for relative, wanted in UPDATES.items():
        rewrite(ROOT / relative, wanted)
    print(f"reconciled {sum(len(v) for v in UPDATES.values())} records across {len(UPDATES)} files")


if __name__ == "__main__":
    main()
