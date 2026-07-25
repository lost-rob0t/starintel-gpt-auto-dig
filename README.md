# StarIntel GPT Auto Dig

Evidence-first research packets produced through GPT-assisted StarIntel loops.

This repository stores bounded dig outputs and machine-readable StarIntel documents. It does not replace canonical design and implementation records in `starintel-auto-research`.

## Repository layout

Each completed loop belongs under:

```text
digs/<target>/<YYYY-MM-DD>-<loop-slug>/
├── README.md
└── records/
    └── *.jsonl
```

The JSONL shards in one packet are non-overlapping parts of one canonical dataset. The build script combines them into a single downloadable `starintel-documents.jsonl`; it also generates Org-roam nodes, backlinks, a source-linked evidence browser, and an interactive exploration graph. Generated Org and HTML output is not checked in or hand-maintained.

## Build and publish

```bash
python -m unittest discover -s tests -v
python scripts/build.py
```

GitHub Actions validates pull requests. Merges to `main` generate and deploy `_site/` through GitHub Pages.

## Git flow

Use the same branch-first workflow as `starintel-auto-research`:

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit only the current dig packet and required generator or validation changes.
4. Open a pull request into `main`.
5. Validate structured documents and inspect the complete diff.
6. Squash-merge when the packet is internally consistent and evidence links resolve.

## Evidence rules

- Separate observed facts, estimates, allegations, analysis, and investigation targets.
- Preserve exact source URLs and retrieval dates.
- Do not convert an inference into a fact.
- Do not infer guilt, command, or conspiracy from institutional proximity alone.
- Record conflicting evidence and counterevidence instead of flattening it away.
- Agent-authored narrative must publish its method, definitions, limits, confidence, and supporting sources.
- Ideological comparisons must test features individually rather than substitute labels.
- Do not present assets under management as personal ownership.
- Do not commit credentials, home addresses, private evidence, or unnecessary personal data.

## StarIntel document baseline

Every JSONL object must include `_id`, `dataset`, `dtype`, `version`, `sources`, `date_added`, and `date_updated`. Relations and analytical assessments must retain enough typed predicates and provenance to reproduce their reasoning path.
