# Palantir federal lobbying enumeration

This pipeline enumerates federal Lobbying Disclosure Act filings naming Palantir as the client. It uses the official `lda.gov` REST API, preserves raw records, collapses superseded quarterly filings, and emits normalized records, summaries, and optional StarIntel event documents.

## Run

```bash
python scripts/enumerate_palantir_lobbying.py \
  --client-name "Palantir Technologies" \
  --dataset palantir-deep-dive-2026-07-25 \
  --output-dir artifacts/palantir-lobbying \
  --emit-starintel
```

Anonymous API access is supported. Set `LDA_API_TOKEN` for the higher authenticated rate limit. The script defaults to the anonymous-safe delay of 4.1 seconds between pages.

For a bounded pass:

```bash
python scripts/enumerate_palantir_lobbying.py \
  --year-start 2025 \
  --year-end 2026 \
  --output-dir artifacts/palantir-lobbying-2025-2026 \
  --emit-starintel
```

For deterministic reprocessing without network access:

```bash
python scripts/enumerate_palantir_lobbying.py \
  --input-jsonl artifacts/palantir-lobbying/raw-filings.jsonl \
  --output-dir artifacts/palantir-lobbying-rebuilt \
  --emit-starintel
```

## Outputs

| File | Purpose |
|---|---|
| `raw-filings.jsonl` | Unmodified API response records |
| `filings-active.jsonl` | Latest active filing per registrant/client/year/quarter plus non-quarterly registrations |
| `filings-superseded.jsonl` | Earlier quarterly reports replaced by later amendments |
| `summary.json` | Machine-readable totals and appearance counts |
| `summary.md` | Human-readable annual, registrant, lobbyist, and agency enumeration |
| `starintel-events.ndjson` | Optional StarIntel 0.9.0 event documents |

## Counting rules

1. A later filing for the same registrant, client, year, and quarter supersedes the earlier filing.
2. In-house Palantir filings use the reported expense field.
3. Outside lobbying firms use the reported income field.
4. Registrations and terminations are preserved but do not contribute to quarterly spending totals.
5. Subcontractor registrations are not automatically added to the prime firm's disclosed income. They require manual review to prevent double counting.
6. The resulting totals are disclosed estimates, not audited invoices.

## Current H1 2026 baseline

The manually verified dataset currently records a disclosed minimum of **$5.91 million** for the first half of 2026:

- Palantir in-house: **$4.06 million**
- Known outside-firm income: **$1.85 million**

Mapped outside firms are Alpine Group Partners, Anchor & Arrow, Ballard Partners, Brownstein Hyatt Farber Schreck, Cornerstone Government Affairs, Ferox Strategies, Invariant, J.A. Green and Company, Miller Strategies, Penn Avenue Partners, Red+Blue Strategies, and Avoq. Northern Compass Group is modeled as a disclosed Brownstein subcontractor and excluded from spending totals unless a separate non-duplicative payment is established.

The main policy clusters are defense appropriations and the NDAA; Army intelligence, readiness, and command-and-control; TITAN, Battlefield Domain Awareness, Multi-Domain Intelligence, and JADC2; Department of Veterans Affairs modernization; public-health data platforms; federal software procurement; aviation and air-traffic control; commercial space and satellite policy; security; and data privacy.

## Interpretation

Lobbying disclosures establish who was retained, which lobbyists worked on an issue, the agencies or chambers contacted, and the amount reported. They can establish issue-to-business alignment. They do not by themselves establish that a government contract was improperly awarded.
