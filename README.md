# StarIntel GPT Auto Dig

Evidence-first StarIntel research packets published as generated Org-roam corpora, source inventories, neutral narratives, and interactive exploration graphs.

## Canonical data rule

Each dig keeps one committed logical source of truth below:

```text
digs/<target>/<YYYY-MM-DD>-<loop-slug>/starintel-documents.jsonl
```

A large stream may be stored as a gzip-compressed, base64-encoded `starintel-documents.jsonl.gz.b64` file or an ordered `.parts` manifest. These are transport forms of the same single JSONL dataset, not duplicate research copies.

`Org` nodes, graph data, source indexes, and the HTML site are derived by `scripts/build_research_site.py`. Generated output is not committed, preventing the research from being duplicated across formats.

## Build locally

```bash
python3 scripts/build_research_site.py \
  --input digs \
  --output _site \
  --org-output .generated/org
```

Open `_site/index.html`.

## Published research

The GitHub Pages workflow validates pull requests and deploys `main`. Each target page contains:

- a neutral evidence-based narrative;
- an interactive exploration graph;
- typed StarIntel record pages;
- generated Org-roam nodes;
- a generated source inventory;
- the canonical JSONL download.

## Git flow

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit one bounded dig or publishing-system change.
4. Open a pull request.
5. Validate JSONL, Org generation, graph generation, and the complete diff.
6. Squash-merge after checks pass.

## Analytical rules

- Separate observed facts, allegations, estimates, analysis, and open probes.
- Preserve exact source URLs and retrieval dates.
- Do not infer control from board membership, contracts, or association alone.
- Do not describe assets under management as personal ownership.
- Use political labels only against explicit defining criteria.
- Record contrary evidence and missing criteria, not only similarities.
- Do not commit credentials, private evidence, home addresses, or unnecessary personal data.
