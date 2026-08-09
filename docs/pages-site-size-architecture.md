# Auto-Dig Pages scaling architecture

Status: implementation in progress

## Current state

The canonical publication path is Nim-first. `scripts/starintel_site.nim` scans the corpus once, keeps the latest canonical record by `_id`, and then materializes several static views. The merge gate in `scripts/validate_for_merge.nim` invokes that generator against the real corpus.

The current generator stores the complete raw record in `Record.raw` and can write the same logical record into multiple physical representations:

1. root `downloads/starintel-complete-corpus.jsonl`;
2. target `downloads/starintel-documents.jsonl`;
3. one or more topic-dataset `downloads/starintel-documents.jsonl` files;
4. target `documents.json` metadata;
5. root `search-index.json` metadata;
6. graph JSON when graph-eligible;
7. target node HTML containing pretty-printed raw JSON when graph-eligible;
8. target public Org containing pretty-printed raw JSON when graph-eligible;
9. topic node HTML containing pretty-printed raw JSON when graph-eligible;
10. topic public Org containing pretty-printed raw JSON when graph-eligible.

A second Org tree is written to `.generated/org`; it is not inside the Pages tree but repeats the same build-time materialization.

`writeTopicDatasets` calls the same target writer used by canonical research targets. Topic membership therefore creates another full export and another set of node/Org surfaces instead of storing membership references.

The browser-side document UI fetches an entire target `documents.json` into memory before pagination or filtering. Root `search-index.json` is also monolithic. This makes browser transfer and memory scale with the corpus even if the Pages byte limit were removed.

## Measurements

Reproduction from the current GitHub Actions merge head against `main`:

- validated input documents: 1,269,476;
- canonical site documents after latest-record resolution: 1,262,786;
- research targets: 53;
- topic datasets: 53;
- generated Pages tree: 10,926,220,320 bytes;
- current configured merge-gate budget: 9,000,000,000 bytes;
- generator wall time in the observed run: about 113.6 seconds, excluding corpus validation;
- merge gate: failed on site bytes.

A recursive byte-class report is being added before generator changes so the same real corpus produces exact HTML, JSON, JSONL, Org, asset, download, file-count, largest-file, largest-directory, canonical-corpus and amplification measurements. Those values will be recorded here after the diagnostic CI run.

## Root causes

Ranked by architectural impact pending the exact byte report:

1. Full canonical payloads are copied into target and topic JSONL exports.
2. Public Org duplicates raw records inside the Pages artifact.
3. Node HTML embeds pretty-printed raw JSON; topic datasets can repeat that materialization.
4. Topic datasets are implemented as full synthetic targets rather than reference manifests.
5. Browser indexes are monolithic and grow with the corpus.
6. The complete bulk corpus is treated as website content even though it is data distribution.

Quasar is not a plausible primary cause: the observed production bundle is measured in megabytes while the Pages tree is measured in gigabytes.

## Regression history

The architecture was already duplicative before the Nim migration. The previous Python builder wrote the complete corpus, per-target full JSONL, public Org, and topic JSONL/Org copies. Topic node pages were lightweight redirects, but the underlying raw-payload duplication already existed.

Commit `d10eba578f2861f77b604062d1984bac3f4edaf5` simultaneously merged the GOP 100k+ expansion and introduced the Nim-first site/merge pipeline. The commit added `scripts/starintel_site.nim` and `scripts/validate_for_merge.nim`, moved Pages generation to Nim, and materialized a much larger GOP corpus. The failure is therefore primarily a latent static-materialization design crossing a scale boundary, with some representation details changed by the Nim port; reverting Nim does not solve the storage model.

## External constraints

GitHub currently documents a 1 GB maximum for a published GitHub Pages site. The Pages deployment artifact has a separate tar-size ceiling of 10 GB; that is not a supported 10 GB website allowance. GitHub explicitly recommends Releases, a CDN, or another host when a Pages site exceeds its quotas.

GitHub Releases are usable without introducing a new hosting provider. A release may contain up to 1,000 assets, each under 2 GiB, with no documented total release-size or bandwidth limit. This makes deterministic compressed corpus shards a workable current bulk-distribution backend and leaves a clean future migration path to object storage because site manifests can carry shard URLs rather than hard-code storage semantics.

Actions artifacts are not suitable as the public canonical data surface: they expire and downloads are tied to workflow-artifact access semantics.

## Alternatives considered

### 1. Deduplicated static Pages only

Store canonical records once under Pages and make targets/topics reference IDs.

Pros: simple hosting, no release publishing step, direct per-record retrieval.

Cons: the canonical corpus itself still grows linearly and eventually exceeds the 1 GB Pages limit. Millions to 100M+ records cannot remain a Pages payload.

Decision: useful as an internal representation rule, insufficient as the complete architecture.

### 2. One dynamic document shell plus canonical static record blobs

Replace per-node HTML with `document.html?id=...` and store canonical record blobs once.

Pros: removes duplicated HTML and preserves stable UI behavior.

Cons: millions of record blobs still create excessive Pages bytes/file counts; 100M records is not credible on Pages.

Decision: use the shell idea, but do not keep the full record store on Pages.

### 3. Pages UI/index metadata plus external bulk shards

Pages contains application shells, CSS/JS, dataset metadata, reference manifests, bounded/sharded indexes, graph projections, source/evidence metadata, and links to external deterministic corpus shards. Releases provide the first bulk backend; the manifest format remains backend-neutral.

Pros: separates website scaling from corpus scaling; overlapping datasets add references rather than raw payload copies; no new infrastructure is required; Releases support large sharded assets; Pages stays far below its supported maximum.

Cons: publication has two coordinated surfaces; direct raw-record rendering needs either a small metadata projection or a future API/range-aware bulk reader; release publishing must be atomic enough that manifests never point to missing assets.

Decision: selected.

### 4. Compression without architectural change

Compress all existing JSONL/Org/HTML output.

Pros: easy byte reduction.

Cons: duplicate payloads remain duplicated, browsers still receive oversized indexes, HTML/Org are not naturally served compressed as downloadable corpus shards, and growth remains multiplicative.

Decision: use compression for bulk distribution only, not as the structural fix.

### 5. Content-addressed record blobs

Store each canonical document by content hash and reference it from datasets.

Pros: maximal cross-dataset deduplication.

Cons: creates a very high file count and operational complexity; canonical `_id` references already solve the observed duplication without a second identity system.

Decision: not needed now.

## Decision

Adopt a split publication model:

- Pages is a bounded UI and metadata/index artifact.
- Full canonical records are emitted once into deterministic bulk shards outside `_site`.
- Target/topic membership is represented by compact references/manifests, not copied full records.
- Per-record HTML is replaced by a shared document-viewer shell where practical.
- Public Org is removed from `_site`; `.generated/org` remains available for repository/research workflows.
- Search/document browsing moves away from one corpus-sized browser download toward deterministic bounded index shards.
- Graph output remains bounded by existing graph limits and is measured separately.
- Evidence-seal semantics remain record-level. The seal follows the canonical bulk corpus/shards rather than requiring the bulk bytes to be located under `_site`.
- The merge gate uses a conservative Pages budget below the supported 1 GB maximum and reports amplification by class.

The bulk manifest will be storage-backend neutral: deterministic shard names, record counts, byte counts, hashes, schema version, compression metadata, and resolved download URLs. GitHub Releases are the first publisher, not part of the canonical data model.

## Expected size

The exact target will be set after the baseline forensic report. Structurally, Pages bytes should become dominated by bounded metadata, graph projections, UI assets, and index shards instead of raw-record multiplication. The goal is substantial headroom below 1 GB, not tuning to the platform ceiling.

## Migration and compatibility

- Existing target and topic landing pages remain.
- Dataset browsing, search, pagination, graph explorer, Quasar, source visibility and evidence status remain available.
- Existing per-target/topic download links become manifest-backed bulk-download entry points rather than duplicate full exports.
- The root complete-corpus link becomes a bulk-download manifest/release link.
- Existing node URLs should redirect or resolve through a shared viewer when keeping them is practical; generating hundreds of thousands of compatibility files is explicitly not acceptable.
- `.generated/org` remains generated; `_site/org` is removed unless a concrete public dependency is discovered.

## Risks

- UI code currently assumes monolithic `documents.json`; index sharding requires coordinated JS changes.
- Evidence-seal tooling currently names a single complete-corpus JSONL path; shard-aware input must preserve per-record Merkle verification and provenance.
- Release publication requires `contents: write` and careful ordering so Pages never advertises absent assets.
- Search semantics may change if static search becomes bounded/prefix-sharded; this must be tested explicitly.
- Quasar integrations may assume existing node/download paths and need compatibility tests.
- A 100M-record corpus may eventually outgrow practical Release operations even though the manifest design remains usable with object storage or the StarIntel server/API.

## Changelog

- 2026-08-09: documented current duplication model, reproduced failure, GitHub platform constraints, regression history, alternatives, and selected split Pages/bulk architecture.
