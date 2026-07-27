# Quasar graph editor inside Auto-Dig

Auto-Dig no longer ships or exposes a second graph interface. Every generated `graph.html` entrypoint redirects to the pinned Quasar application and opens its `/graph` route.

## Runtime ownership

- Auto-Dig generates the dataset JSONL files.
- The same-origin host bridge reads the selected dataset and returns its StarIntel documents.
- Quasar imports missing documents into its local PouchDB corpus.
- Existing Quasar documents are not replaced during reload, so edits remain authoritative.
- Quasar owns graph workspaces, document changes, relations, and browser persistence.
- The host shell contains only the full-screen Quasar iframe. It has no graph toolbar, graph canvas, or duplicate navigation.

## Dataset mapping

- The complete corpus loads from `downloads/starintel-complete-corpus.jsonl`.
- A named dataset loads from `<dataset>/downloads/starintel-documents.jsonl`.
- Generated dataset graph pages redirect to `quasar/index.html?dataset=<dataset>`.
- The root graph page redirects with `dataset=complete-corpus`.

## Pinned build

`quasar-fork.lock.json` records the exact `lost-rob0t/auto-dig-quasar` commit built into the research site. The Pages workflow checks out that commit, runs the fork validation, builds it with `/quasar/app/` as its base path, generates Auto-Dig, and then replaces the legacy graph entrypoints.

## Local build

```bash
pin=$(python3 -c 'import json; print(json.load(open("quasar-fork.lock.json"))["quasar_fork_commit"])')
git clone https://github.com/lost-rob0t/auto-dig-quasar.git .quasar-fork
git -C .quasar-fork checkout "$pin"
npm --prefix .quasar-fork ci
VITE_BASE_PATH=/quasar/app/ npm --prefix .quasar-fork run build

python3 scripts/build_research_site.py \
  --input digs \
  --db db \
  --output _site \
  --org-output .generated/org

python3 scripts/build-auto-dig-quasar.py \
  --auto-dig-root . \
  --site-dir _site \
  --quasar-dist .quasar-fork/dist \
  --quasar-fork-commit "$pin" \
  --quasar-upstream-commit "$(python3 -c 'import json; print(json.load(open("quasar-fork.lock.json"))["quasar_upstream_commit"])')"
```

Open any generated dataset's `graph.html`. It immediately transfers to the Quasar graph editor with that dataset populated in Quasar's database.
