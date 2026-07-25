# StarIntel GPT Auto Dig

Evidence-first research packets produced through GPT-assisted StarIntel loops and published through the Python research-site generator.

This repository stores bounded dig packets, normalized StarIntel records, source inventories, reports, manifests, and optional Org research notes. It does not replace the canonical design and implementation records in `starintel-auto-research`.

## Repository layout

Research may be published in either of two compatible forms.

Packet-oriented digs live under:

```text
digs/<target>/<YYYY-MM-DD>-<loop-slug>/
├── README.md
├── sources.md
└── starintel-documents.jsonl
```

Normalized records live under:

```text
db/<dtype>/<_id>.ndjson
```

Each normalized file contains exactly one compact JSON object plus one terminating newline. Its directory and filename must match the record's `dtype` and `_id` exactly.

Supporting material may live under:

- `manifests/` — dataset manifests and integrity metadata
- `reports/` — readable research reports
- `roam/research/` and `roam/indexes/` — optional Org research and index nodes
- `scripts/` — validation and Python site-generation tooling

A packet may add fixtures, manifests, compressed transport files, or exports when required. Generated files must remain beside the packet or dataset that produced them.

Multiple packets may exist for the same target. The Python generator merges packet records by stable document ID and `date_updated`, preserving the target's research history.

## Generated research site

The canonical publisher is Python:

```bash
python3 scripts/build_research_site.py \
  --input digs \
  --output _site \
  --org-output .generated/org
```

The GitHub Pages workflow validates pull requests and deploys `main`. Generated output is not committed.

Each generated target page can contain:

- a neutral evidence-based narrative
- an append-only agent research ledger
- an evidence-posture summary
- an interactive exploration graph
- typed StarIntel record pages
- generated source and packet indexes
- a merged canonical JSONL download

The repository does not use an Emacs-based Pages deployment workflow.

## Agent research ledger

An agent may publish its synthesis as a `research-pass` document inside a packet. A research pass should expose:

- the research question
- method and classification rules
- findings with confidence
- supporting record IDs
- counterevidence or competing interpretations
- unresolved investigation-target IDs
- source records and retrieval dates
- the agent identity and narrative role

Research passes are append-only. A later pass supplements or challenges earlier analysis instead of silently replacing it.

## Git flow

Use the same branch-first workflow as `starintel-auto-research`:

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit only the current research packet or dataset and its required publishing or validation changes.
4. Open a pull request into `main`.
5. Validate structured documents, generated output, and the complete diff.
6. Squash-merge when the packet is internally consistent and evidence links resolve.

Do not publish a research packet directly to `main`.

## Evidence and analytical rules

- Separate observed facts, allegations, estimates, analysis, recommendations, and open probes.
- Preserve exact source URLs and retrieval dates.
- Do not convert an inference into a fact.
- Do not infer control from board membership, contracts, or association alone.
- Do not describe assets under management as personal ownership.
- Use political labels only against explicit defining criteria.
- Record contrary evidence and missing criteria, not only similarities.
- Do not fabricate sources, confidence, test results, commits, or workflow status.
- Use stable document IDs and preserve conflicting evidence.
- Do not commit credentials, private evidence, home addresses, or unnecessary personal data.

## StarIntel document baseline

Every logical JSONL record must include:

- `_id`
- `dataset`
- `dtype`
- `version`
- `sources`
- `date_added`
- `date_updated`

Relation records must preserve their predicate, endpoints, sources, and confidence using the schema version declared by the packet.
