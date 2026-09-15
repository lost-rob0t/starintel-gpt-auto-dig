# Rensselaer County Sheriff — Parma incoming-sharing snapshot

Issue: #1901
Worker: 5/8

This bounded pass extends the already-landed Rensselaer County Sheriff's Office Flock sharing harvest with one non-duplicated current public-portal observation.

## Added evidence

The **Parma OH PD Flock Transparency Portal**, labeled last updated **July 23, 2026**, lists **`Rensselaer County NY SO`** under **Sharing Network Data With**. On the Flock portal this field is described as organizations granted access to Parma OH PD data.

Source:
- https://transparency.flocksafety.com/parma-oh-pd

Corpus/issue dedupe found the prior canonical #1901 harvest contains other incoming-sharing examples but not this Parma OH PD observation.

## Evidence boundary

This packet records only the directed public-portal snapshot:

`Parma OH PD -> lists Rensselaer County NY SO as a sharing recipient`

It does **not** establish:

- reciprocity or any `RCSO -> Parma` share;
- the approval actor or effective/start/end dates;
- native `SharedNetworks`, Network Audit, or Organization Audit state;
- any RCSO user/account identity;
- any actual RCSO search/query against Parma data.

The portal is vendor-published evidence, not a native tenant audit export. Those unresolved platform-control and usage questions remain under the existing #1901 sharing/audit targets.

## Canonical records

- `starintel:analysis:rensselaer-sheriff-parma-incoming-share-request-1901-2026-09-15`
- `starintel:research-pass:request-1901-parma-incoming-share-2026-09-15`

The packet JSONL is authored outside `db/`. Normalized `db/` records are materialized only through the repository's canonical `python3 scripts/starintel.py import ...` path before the PR is opened.
