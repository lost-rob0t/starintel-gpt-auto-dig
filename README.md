# StarIntel GPT Auto Dig

Evidence-first research packets produced through GPT-assisted StarIntel loops.

This repository stores bounded dig outputs, source inventories, and machine-readable StarIntel documents. It does not replace the canonical design and implementation records in `starintel-auto-research`.

## Repository layout

Each completed loop belongs under:

```text
digs/<target>/<YYYY-MM-DD>-<loop-slug>/
├── README.md
├── sources.md
└── starintel-documents.jsonl
```

A packet may add supporting fixtures or exports when the dig requires them. Generated files must stay beside the packet that produced them.

## Git flow

Use the same branch-first workflow as `starintel-auto-research`:

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit only the current dig packet and its required validation changes.
4. Open a pull request into `main`.
5. Validate structured documents and inspect the complete diff.
6. Squash-merge when the packet is internally consistent and evidence links resolve.

Do not publish a research packet directly to `main`. The initial repository bootstrap is the sole exception because an empty Git repository has no commit from which a branch can be created.

## Evidence rules

- Separate observed facts, analysis, and recommendations.
- Preserve exact source URLs and retrieval dates.
- Do not convert an inference into a fact.
- Do not fabricate sources, confidence, test results, commits, or workflow status.
- Use stable document IDs.
- Relation records must declare a predicate plus source and destination document IDs.
- Record conflicting evidence instead of flattening it away.

## StarIntel document baseline

`starintel-documents.jsonl` contains one JSON object per line. Every object must include:

- `_id`
- `dataset`
- `dtype`
- `version`
- `sources`
- `date_added`
- `date_updated`

Relation documents must also include:

- `predicate`
- `source_id`
- `destination_id`
- `confidence`

The current packet controls any additional fields required for its target.
