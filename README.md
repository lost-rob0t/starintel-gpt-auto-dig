# StarIntel GPT Auto Dig

Evidence-first research packets produced through GPT-assisted StarIntel loops and published as generated Org-roam corpora, source inventories, neutral narratives, agent research ledgers, and interactive exploration graphs.

This repository stores bounded dig outputs and machine-readable StarIntel documents. It does not replace the canonical design and implementation records in `starintel-auto-research`.

## Repository layout

Each completed loop belongs under:

```text
digs/<target>/<YYYY-MM-DD>-<loop-slug>/
├── README.md
└── starintel-documents.jsonl
```

A packet may add supporting fixtures, manifests, or exports when required. A large canonical stream may be stored as a gzip-compressed, base64-encoded `starintel-documents.jsonl.gz.b64` file or an ordered `.parts` manifest. These are transport forms of one logical JSONL dataset, not duplicate research copies.

Multiple packets may exist for the same target. The generator merges them by stable document ID and `date_updated`, preserving the target's complete history. The generated canonical download contains the merged target corpus rather than only the newest incremental packet.

## Agent research ledger

An agent may publish its synthesis as a `research-pass` document inside a later packet. A research pass should expose:

- the research question;
- method and classification rules;
- findings with confidence;
- supporting record IDs;
- counterevidence or competing interpretations;
- unresolved investigation-target IDs;
- source records and retrieval dates;
- the agent identity and narrative role.

Research passes are append-only. A later pass supplements or challenges earlier analysis instead of silently replacing it. The site renders these passes as an evidence-linked narrative ledger.

## Generated research site

`Org` nodes, graph data, source indexes, and HTML are derived by `scripts/build_research_site.py`. Generated output is not committed.

```bash
python3 scripts/build_research_site.py \
  --input digs \
  --output _site \
  --org-output .generated/org
```

Open `_site/index.html`. The GitHub Pages workflow validates pull requests and deploys `main`. Each target page can contain:

- a neutral evidence-based narrative;
- an append-only agent research ledger;
- an evidence-posture summary;
- an interactive exploration graph;
- typed StarIntel record pages;
- generated Org-roam nodes;
- a generated source inventory;
- the merged canonical JSONL download;
- the ordered research-packet history.

## Git flow

Use the same branch-first workflow as `starintel-auto-research`:

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit only the current dig packet and its required publishing or validation changes.
4. Open a pull request into `main`.
5. Validate structured documents, generated Org, graph output, and the complete diff.
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
