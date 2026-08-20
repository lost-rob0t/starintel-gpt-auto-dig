# Auto-Dig Pages scaling architecture

Status: implemented in PR #2005; production deployment pending merge

## Executive result

The Pages regression was not a Quasar problem and not fundamentally a Nim problem. Auto-Dig was publishing the same logical corpus repeatedly as complete JSONL, per-target JSONL, topic JSONL, public Org, raw-record node HTML, and large browser indexes. The older Python generator already had most of that duplication; the August 2026 GOP expansion and Nim-first migration pushed the latent design past the platform limit.

The fix separates the website from the data distribution layer:

- GitHub Pages contains bounded UI, bounded previews, bounded graph projections, source/evidence surfaces, manifests, and a compact range-index map.
- GitHub Releases contain the canonical corpus shards, dataset membership lists, and range-addressable search/record-index bundles.
- Overlapping datasets now reference canonical document IDs instead of copying complete records.
- Browsers request bounded byte ranges from immutable index bundles rather than downloading corpus-sized JSON.

On the same real corpus, the merge-gate Pages tree fell from **10,926,220,412 bytes to 43,914,441 bytes**, a **99.60% reduction** and about **248.8x smaller**. File count fell from **348,112 to 926**.

## Reproduced baseline

The forensic pass was run before changing generation behavior against the real PR merge head.

| Metric | Baseline |
|---|---:|
| Validated input documents | 1,269,476 |
| Canonical documents | 1,262,786 |
| Research targets | 53 |
| Topic datasets | 53 |
| Pages bytes | 10,926,220,412 |
| Files | 348,112 |
| HTML bytes | 581,209,526 |
| JSON bytes | 1,760,656,239 |
| JSONL bytes | 8,228,865,459 |
| Org bytes | 355,290,248 |
| Canonical corpus bytes | 2,735,820,082 |
| Largest directory | `dataset-gop` — 2,742,579,297 bytes |
| Site/corpus amplification | 3.9938x |
| Configured merge budget | 9,000,000,000 bytes |
| Result | FAIL |

The old 9 GB gate was not a safe Pages policy. GitHub documents a 1 GB maximum for a published Pages site; the separate 10 GB deployment-artifact ceiling is not a supported 10 GB website allowance.

The baseline generator itself took roughly 114 seconds after corpus validation. The dominant failure was storage amplification, not generator CPU time.

## Root cause ranking

1. **Repeated full JSONL exports.** JSONL alone accounted for 8.23 GB of the 10.93 GB Pages tree.
2. **Topic datasets were synthetic full targets.** `writeTopicDatasets` reused the target writer, multiplying raw payloads when records belonged to overlapping views.
3. **Raw records were embedded again in public Org and node HTML.** HTML plus Org added about 936 MB.
4. **The complete corpus was treated as website content.** A 2.74 GB canonical data product cannot be a GitHub Pages file tree even if every duplicate is removed.
5. **Browser indexes were corpus-sized.** Pagination happened only after large JSON files had already been downloaded and parsed.
6. **The merge gate encoded the wrong platform model.** It allowed 9 GB instead of preserving substantial headroom below the supported Pages maximum.

Quasar was measured in megabytes and passed its full test/build suite throughout the repair. It was not a material contributor to the regression.

## Regression history

The duplication model predates the Nim port. The prior Python builder already emitted the complete corpus, per-target full JSONL, public Org, and topic JSONL/Org copies.

Commit `d10eba578f2861f77b604062d1984bac3f4edaf5` merged the GOP 100k+ expansion while making the Nim site/merge pipeline canonical. That commit exposed the scale failure because the corpus became materially larger at the same time the new generator was adopted. Reverting Nim would retain the underlying materialization model and merely move the failure back to Python.

During implementation, Nim 2.2 also caught unsafe local-procedure captures in the new generator work. Those were fixed at source level; the final code builds normally under Nim 2.2.4 with ORC and does not rely on `nimNoLentIterators`.

## Architecture

### Pages: bounded presentation layer

Pages now contains:

- target and topic landing pages;
- bounded `documents.json` previews, capped at 2,000 records per surface;
- bounded graph projections: 20,000 documents for canonical targets and 5,000 for topic datasets;
- source summaries;
- evidence-seal receipt and verification UI;
- dataset/topic manifests;
- Quasar assets;
- a small `search-index.json` range map;
- shared document/search UI instead of one raw-record HTML file per document.

Pages explicitly does **not** contain:

- the complete raw JSONL corpus;
- per-target or per-topic `starintel-documents.jsonl` copies;
- public raw-record Org trees;
- corpus-linear record/search index files;
- hundreds of thousands of generated node HTML files.

The merge gate rejects regressions that reintroduce `_site/org`, `_site/indexes`, or per-view `starintel-documents.jsonl` and enforces a **200 MB Pages budget**.

### Releases: immutable bulk/data layer

The build emits one canonical corpus stream and deterministic raw shards outside `_site`. Publication then creates an immutable GitHub Release keyed to the main commit.

Release assets contain:

- deterministic gzip-compressed canonical JSONL shards;
- deterministic gzip-compressed target/topic membership lists containing canonical IDs only;
- uncompressed range-addressable record-index bundles;
- uncompressed range-addressable search-index bundles;
- a release manifest containing sizes, hashes, record counts, and URLs.

Corpus shards are kept below 1.5 GB raw so their corresponding Release assets remain comfortably below GitHub's per-asset limit. The manifest format is backend-neutral: GitHub Releases are the first storage backend, not part of the canonical data model.

### Search and document lookup

The Nim generator still creates temporary record/search index files during the build. `scripts/externalize_search_indexes.py` then compacts them into Release bundles and deletes `_site/indexes` before Pages validation.

The browser-side protocol is deliberately bounded:

1. Pages serves `search-index.json`, which maps logical index segments to immutable bundle byte ranges.
2. Search uses two-character token prefixes, but each prefix is split by dataset/target scope into segments of at most **16 MB**.
3. Target/topic search fetches only segments for that scope.
4. Global search stops reading segments after it has enough candidate ordinals rather than downloading the whole posting set.
5. Record metadata lives in ordered pages inside a record bundle.
6. Exact `?id=...` links binary-search page `first_id`/`last_id` bounds, then fetch one record-page range.
7. The browser requires HTTP `206 Partial Content`; if a host ignores `Range`, it refuses the response rather than accidentally downloading a whole multi-hundred-megabyte bundle.

Production CI creates the Release before publishing Pages and smoke-tests both a search range and a record range, including browser CORS and JSON reconstruction.

## Final real-corpus measurements

The final PR gate ran against the same 1,262,786 canonical records.

| Metric | Baseline | Deduplicated Pages v1 | Final range-bundle architecture |
|---|---:|---:|---:|
| Pages bytes | 10,926,220,412 | 433,011,663 | **43,914,441** |
| Files | 348,112 | 2,447 | **926** |
| JSONL bytes in Pages | 8,228,865,459 | 0 | **0** |
| Org bytes in Pages | 355,290,248 | 0 | **0** |
| Site/corpus amplification | 3.9938x | 0.1583x | **0.0161x** |
| Range-index bytes outside Pages | n/a | n/a | **391,217,099** |
| Range-index bundles | n/a | n/a | **2** |
| Membership files outside Pages | n/a | 106 | **106** |
| Corpus shards | n/a | 2 | **2** |
| Result | FAIL | PASS | **PASS** |

The intermediate 433 MB result proved that raw corpus duplication had been removed, but it was intentionally not accepted as the final architecture because 391 MB of search metadata still grew with record count. Externalizing that index reduced Pages by another ~389 MB.

The final merge-gate build reported:

- 1,269,476 validated input documents;
- 1,262,786 canonical documents;
- 53 targets and 53 topic datasets;
- 10,639 bounded search segments;
- maximum search segment size 16 MB;
- 43,914,441 Pages bytes before Quasar is installed by the production workflow;
- 391,217,099 range-index bytes outside Pages;
- 2 corpus shards;
- 106 membership files;
- 2 range-index bundles;
- full merge gate PASS.

Generation of the deduplicated site/bulk intermediate took about 84 seconds in that run; index externalization took about 5 seconds. Corpus validation remained the largest single CI stage at roughly 154 seconds.

## Scale model

At the current corpus the observed averages are approximately:

- canonical raw payload: 2,166.5 bytes per record;
- externalized record/search metadata: 309.8 bytes per record.

A naive linear projection to 100 million records is therefore roughly:

- **216.6 GB raw canonical corpus**;
- **31.0 GB externalized index data**;
- about **145** 1.5 GB raw corpus shards before compression;
- about **21** 1.5 GB index bundles;
- plus dataset membership assets and manifests.

Using today's 106 membership surfaces, that is on the order of 273 Release assets, below the current 1,000-assets-per-release limit. This is an order-of-magnitude planning estimate, not a capacity guarantee: record size, dataset count, search-token distribution, and compression ratios can all change.

The important property is that those corpus-linear bytes no longer live in Pages. Pages growth is dominated by explicitly bounded previews/graphs plus metadata for datasets and range segments rather than raw document count.

### What is *not* yet 100M-safe

The publication/storage model is designed to stop Pages from being the limiting factor, but the current Nim generator is **not yet a credible 100M-record build engine**. `Record.raw` and canonical tables are still retained in memory while scanning and resolving latest records. A 100M build requires a later phase using an external sort/spool, SQLite/LMDB-style temporary index, or the StarIntel server/database so canonicalization and topic membership do not require holding the full raw corpus in RAM.

GitHub Releases are also an intentionally replaceable first backend. At approximately one billion records, the current 1.5 GB sharding model would exceed the practical 1,000-asset release envelope even before memberships. Long before that point, the same manifests should point to object storage or the StarIntel server/API. No Pages/UI format change is required for that migration.

## Evidence integrity

Evidence sealing remains record-level and is computed over the single canonical bulk stream before publication. The verification page no longer assumes the corpus bytes live under `_site`; it links the canonical corpus manifest and bulk-release manifest and documents deterministic reconstruction of the ordered shards.

This preserves the important invariant: moving bytes out of Pages changes transport, not the canonical records, hashes, evidence metadata, or Merkle commitment.

## Compatibility

Preserved and tested:

- target and topic landing pages;
- dataset browsing;
- document search and pagination;
- exact document deep links through `documents.html?id=...`;
- graph explorer and graph node navigation;
- source visibility;
- evidence-seal publication and verification;
- Quasar build/integration path;
- `.generated/org` for repository/research workflows.

Legacy per-node static files are not regenerated. A compatibility 404 route redirects old `/nodes/...html` navigation toward the shared document browser rather than recreating hundreds of thousands of files.

## CI / deployment invariants

PR CI now runs the canonical Nim path and tests the pinned Quasar frontend, repository UI regressions, Nim compilation, synthetic overlapping-topic deduplication, range-bundle reconstruction, and the full real-corpus merge gate.

Production CI additionally:

1. builds and validates the corpus;
2. creates the bounded Pages tree and bulk intermediates;
3. externalizes search/record indexes;
4. packages deterministic Release assets;
5. seals and verifies the canonical corpus;
6. builds and installs Quasar;
7. enforces the final Pages byte budget;
8. creates the immutable bulk Release;
9. verifies live Release byte-range/CORS behavior;
10. uploads and deploys Pages.

The Release is created before Pages is uploaded so the deployed site cannot intentionally advertise a not-yet-created bulk version.

## Remaining risks

- The generator's in-memory canonicalization is the next scale bottleneck; it must be externalized before a real 100M run.
- Release bandwidth and upload time may become operationally expensive well before hard asset-count limits are reached.
- Range transport depends on the Release download path honoring byte ranges and browser CORS; production CI fails before Pages deployment if that contract is not observed.
- Search is intentionally candidate-bounded for browser safety. Extremely broad global queries may not enumerate every possible match; analytical full-corpus search belongs in the server/API path.
- Graph projections remain deliberately capped for interactive usability; complete graph analytics should use the canonical corpus/server rather than browser JSON.
- Dataset count itself is not bounded by document count. If thousands of new target/topic surfaces are added, preview/manifest overhead should be re-evaluated independently.

## Changelog

- 2026-08-09: reproduced the 10.93 GB failure and recorded byte-class amplification.
- 2026-08-09: confirmed duplication predated Nim and identified the GOP/Nim merge as the scale-crossing event rather than the architectural origin.
- 2026-08-09: removed complete/per-view raw corpus bytes, public Org, and raw node HTML from Pages; converted dataset overlap to canonical-ID membership references.
- 2026-08-09: added bounded previews, shared document routing, and external bulk corpus shards.
- 2026-08-09: externalized corpus-linear search/record indexes into range-addressable Release bundles with 16 MB search-segment caps.
- 2026-08-09: final real-corpus gate passed at 43,914,441 Pages bytes, 0.0161x amplification, and 926 files.
- 2026-08-09: tightened the Pages merge/deploy budget to 200 MB, leaving more than 4.5x headroom over the measured pre-Quasar PR artifact and substantial margin below GitHub's supported 1 GB maximum.
