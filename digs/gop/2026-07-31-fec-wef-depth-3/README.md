# GOP FEC and WEF recursion — depth 3

This reproducible pass resolves the four queued depth-3 targets from the WEF/Palantir/AIPAC branch.

## Official inputs

- FEC 2025–2026 committee master, candidate master, committee-to-committee transaction, and independent-expenditure bulk files.
- Official WEF Annual Meeting partner pages for 2024–2026 and the official January 20, 2026 Alex Karp session.
- Existing canonical WEF partner records are used when a live WEF page is client-rendered or unavailable.

## Transaction handling

- Transactions are keyed by filer plus transaction ID when available.
- The highest file number and record ID select the latest row.
- Amendment and prior-file provenance remain in relation qualifiers.
- Memo rows remain represented but are excluded from the pass's non-memo aggregate figures.
- Direct committee disbursements, independent expenditures, vendors, candidate support/opposition, and WEF participation are separate edge types.

## Output

- Canonical packet: `starintel-documents.jsonl`
- Run report: `reports/gop-fec-wef-depth-3.json`
- Completed depth-3 targets: 4
- Queued depth-4 targets: 4

The packet must be imported through `python3 scripts/starintel.py import ... --replace`; normalized DB records are never hand-written by this generator.
