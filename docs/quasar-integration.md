# Quasar graph editor inside AutoDig

AutoDig no longer ships or exposes a second graph interface. Every generated `graph.html` entrypoint redirects to the pinned Quasar application and opens its `/graph` route.

## Runtime ownership

- AutoDig generates the dataset JSONL files.
- `lost-rob0t/quasar` owns the runtime pin, Common Lisp control-plane bridge, and pinned `quasar-ui` frontend submodule.
- The optional AutoDig host adapter is injected by Quasar's `scripts/prepare-frontend.sh`.
- The same-origin AutoDig host bridge reads the selected dataset and returns its StarIntel documents.
- Quasar imports missing documents into its local PouchDB corpus through the normal application store.
- Existing Quasar documents are not replaced during reload, so edits remain authoritative.
- Quasar owns graph workspaces, document changes, relations, and browser persistence.
- The AutoDig host shell contains only the full-screen Quasar iframe. It has no graph toolbar, graph canvas, or duplicate navigation.

The AutoDig adapter activates only when the iframe URL contains `?host=auto-dig`. Normal standalone and CLOG-hosted Quasar sessions do not start the AutoDig protocol.

## Dataset mapping

- The complete corpus loads from `downloads/starintel-complete-corpus.jsonl`.
- A named dataset loads from `<dataset>/downloads/starintel-documents.jsonl`.
- Generated dataset graph pages redirect to `quasar/index.html?dataset=<dataset>`.
- The root graph page redirects with `dataset=complete-corpus`.

## Pinned build

`quasar-fork.lock.json` now records two exact revisions despite retaining its historical filename:

- `quasar_commit`: the `lost-rob0t/quasar` runtime and frontend-overlay commit.
- `quasar_ui_commit`: the `frontend/` submodule revision expected by that Quasar commit.

The Pages workflow checks out Quasar recursively, verifies both revisions, prepares the frontend overlays, validates and builds the frontend with `/quasar/app/` as its base path, generates AutoDig, and replaces the legacy graph entrypoints.

The retired `lost-rob0t/auto-dig-quasar` full UI fork is no longer part of the deployment path.

## Local build

```bash
quasar_commit=$(python3 -c 'import json; print(json.load(open("quasar-fork.lock.json"))["quasar_commit"])')
quasar_ui_commit=$(python3 -c 'import json; print(json.load(open("quasar-fork.lock.json"))["quasar_ui_commit"])')

git clone --recurse-submodules https://github.com/lost-rob0t/quasar.git .quasar
git -C .quasar checkout "$quasar_commit"
git -C .quasar submodule update --init --recursive

test "$(git -C .quasar/frontend rev-parse HEAD)" = "$quasar_ui_commit"
bash .quasar/scripts/prepare-frontend.sh
npm --prefix .quasar/frontend ci
VITE_BASE_PATH=/quasar/app/ npm --prefix .quasar/frontend run build

python3 scripts/build_research_site.py \
  --input digs \
  --db db \
  --output _site \
  --org-output .generated/org

python3 scripts/build-auto-dig-quasar.py \
  --auto-dig-root . \
  --site-dir _site \
  --quasar-dist .quasar/frontend/dist \
  --quasar-commit "$quasar_commit" \
  --quasar-ui-commit "$quasar_ui_commit"
```

Open any generated dataset's `graph.html`. It transfers to the new Quasar graph editor with that dataset populated in Quasar's local corpus.
