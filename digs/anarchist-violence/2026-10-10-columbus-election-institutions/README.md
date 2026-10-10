# Columbus election institutions: bounded packet adaptation

This packet contains **13 existing observations**: six public institutions or
organizations, five official webpage observations, one institutional relation,
and one review finding. It adapts already-collected material to the maintained
published StarIntel runtime. It does not perform another research pass, identify
individuals, collect voter records, infer political beliefs, or import records
into the main database.

The historical `anarchist-violence` dataset/root name is retained for continuity.
It does **not** imply that these institutions or civic organizations are involved
in violence or wrongdoing. Ohio Voice and the Ohio Voter Rights Coalition are
state-level context; no Columbus membership or local affiliation is inferred.

## Authority and artifacts

- Published StarLang release: `0.10.1`, commit
  `765f1673851192bcaf1cdd2f35c47608f979b079`.
- Maintained Python runtime: `lost-rob0t/starintel-doc` at
  `ac015a5d92a1d9587e5dc7764dd9e0a150a6d0a8`.
- `starintel-documents.jsonl`: canonical flat wire packet, generated only through
  this repository's `scripts/starintel.py create --fields` CLI.
- `adaptation-receipt.json`: per-record field accounting, exact artifact hashes,
  retained IDs, mapping rules, and archive-only values.
- `generate-packet.py`: deterministic generator and no-write `--check` verifier.
- [Exact original artifact](../../../reports/archives/2026-10-10-columbus-election-institutions/original-unpublished-packet.jsonl.txt):
  original unsupported packet bytes, including the full research-pass receipt.
  Its `.jsonl.txt` suffix and location outside `digs/` and `db/` make its archival,
  non-canonical status explicit. It must never be imported as published wire data.

Original SHA-256:
`6811aa5d3f0f171f9a7d8493571a7363cccad21e0761eb7115c74249823b9b48`.

## Deliberate mapping

The original draft used `source` and `research-pass`, which are not supported by
the pinned published 60-dtype release. Relabeling the draft as canonical would be
incorrect. This adaptation uses only existing schema fields:

- Six `org` records and the `relation` keep every original field and fact.
- Five `source` observations become `url` records. `url` is unchanged; `title`
  becomes `contentTitle`; `retrievedAt` becomes `fetchedAt` and
  `sourceRetrievedAt` as integer Unix seconds. The exact fractional timestamp,
  `accessMethod`, and `kind` remain inspectable in the original archive.
- The `research-pass` becomes one `finding`: `researchQuestion` becomes `title`,
  the single original finding description becomes `description`, and the twelve
  `supportingRecordIds` become typed `evidence` references. Original draft status
  is retained. This is the review's result, not a claim that a canonical
  research-pass receipt exists. The full receipt, method, iteration, termination
  reason, empty counterevidence and unresolved-target lists, and agent identity
  remain in the archive.
- All 13 original IDs remain stable, including the `source` and `research-pass`
  prefixes after dtype changes. Reference `schema` values use the actual new
  dtypes. This is a documented correction of the same observations, not creation
  of new identities. Before adding this packet, the repository corpus reader
  examined 1,315,873 existing documents at Auto-Dig head
  `fea86e4f08e37a6fcadbe28cfc173675caed71ee`; none used these 13 IDs.
- Each `org`, `relation`, and `finding` cites exactly the URL records matching
  its original `sourceUrls`. The URL observations retain their original URLs and
  retrieval provenance but have empty `sources`; they do not fabricate
  independent corroboration by citing themselves. The validator's `unverifed`
  output therefore legitimately includes those five URL observations.
- Every record has `visibility` and `sensitivity` set to `public`, `sourceKinds`
  set to `["web"]`, and `createdAt` / `updatedAt` equal to original `collectedAt`.
  Adaptation does not represent a fresh collection or verification time.
- No unsupported field is hidden in `extensions`, `metadata`, `raw`, or
  `provenance`. The combination of canonical packet, exact original archive, and
  mapping receipt preserves the original information; the canonical projection
  alone deliberately does not represent the full unsupported receipt.

## Reproduction and validation

Run from the repository root with the pinned dependency installed. For a
materialized checkout of the exact runtime, set `PYTHONPATH` to that checkout
(for example, `export PYTHONPATH=../python-runtime-current`). The generator
checks the control file, authority locks, generated release, and 60-dtype
inventory before creating records; it stops if any of these disagree.

```bash
python3 digs/anarchist-violence/2026-10-10-columbus-election-institutions/generate-packet.py
python3 digs/anarchist-violence/2026-10-10-columbus-election-institutions/generate-packet.py --check
python3 -m unittest discover -s tests -p test_columbus_institution_packet.py -v
git diff --check
```

The regression suite validates source fidelity, exact archival and output
hashes, complete field accounting, stable unique IDs, supported dtypes, strict
published-schema validation, source/evidence/endpoint resolution, public
metadata, reproducibility, and transactional import into an automatically
removed temporary database. It does not write into the main `db/`.

These packet-level checks do not replace the repository's mandatory native
full merge gate (`nimble buildFast` followed by `bin/validate-for-merge --site`)
or current-head required GitHub checks. Keep publication/merge readiness
separate from successful draft generation.
