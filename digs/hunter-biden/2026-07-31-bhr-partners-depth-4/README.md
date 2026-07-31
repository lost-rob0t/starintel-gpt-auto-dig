# Hunter Biden — BHR Partners 2023 management-company cap table

**Dataset:** `hunter-biden`  
**Run:** `2026-07-31-bhr-partners-depth-4`  
**Schema:** StarIntel v0.9.0  
**Status:** depth-4 document-derived packet; contract execution unverified

## What this pass adds

This pass extracts the surfaced 2023 amended BHR joint-venture contract copy while preserving its evidentiary limitations.

The copy lists:

- a distinct Shanghai private-fund management company operating under the BHR Partners name;
- registered capital of **RMB 30 million**;
- Angju at **40% / RMB 12 million**;
- Shanghai Ample Harvest at **30% / RMB 9 million**;
- Ulysses at **10% / RMB 3 million**;
- Skaneateles at **10% / RMB 3 million**;
- Thornton at **10% / RMB 3 million**;
- P. Kevin Morris as Skaneateles's authorized representative and managing member;
- Krista Ammirati Archer as Ulysses's authorized representative and managing member;
- a seven-director board, with Angju appointing three, Ample Harvest two, and Ulysses/Skaneateles/Thornton jointly appointing two.

## Evidence boundary

The publicly surfaced copy contains a blank 2023 signature date and blank signature fields in the indexed text. Its execution, filing status, and chain of custody are not independently verified.

Every relation derived only from that copy is therefore marked `source-qualified` and uses predicates such as `listed_as_*`, not unconditional current-state assertions.

## Analytic value

The document clarifies why a 10 percent registered-capital block could be approximately **RMB 3 million** while the platform reported much larger assets or portfolio exposure: the percentage concerns the **management company**, not 10 percent of assets under management.

## Counts

- Sources: 1
- Organizations: 4
- People: 2
- Relations: 14
- Investigation targets: 4
- Total: 25

## Files

1. `sources.jsonl`
2. `entities.jsonl`
3. `relations-1.jsonl`
4. `relations-2.jsonl`
5. `investigation-targets.jsonl`
6. `sources.md`
7. `manifest.json`
