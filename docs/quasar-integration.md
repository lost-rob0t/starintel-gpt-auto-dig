# Quasar graph editor inside AutoDig

AutoDig no longer ships or exposes a second graph interface. Every generated `graph.html` entrypoint redirects to the pinned Quasar application and opens its `/graph` route.

## Runtime ownership

- AutoDig generates the canonical corpus, bounded browser projections, and Quasar working sets.
- `lost-rob0t/quasar` owns the runtime pin, Common Lisp control-plane bridge, and pinned `quasar-ui` frontend submodule.
- The optional AutoDig host adapter is injected by Quasar's `scripts/prepare-frontend.sh`.
- The same-origin AutoDig host bridge reads the selected bounded working set and returns real StarIntel documents from the canonical corpus.
- Quasar imports missing documents into its local PouchDB corpus through the normal application store.
- Existing Quasar documents are not replaced during reload, so edits remain authoritative.
- Quasar owns graph workspaces, document changes, relations, and browser persistence.
- The AutoDig host shell contains only the full-screen Quasar iframe. It has no graph toolbar, graph canvas, or duplicate navigation.

The AutoDig adapter activates only when the iframe URL contains `?host=auto-dig`. Normal standalone and CLOG-hosted Quasar sessions do not start the AutoDig protocol.

## Dataset mapping

The complete canonical corpus is too large to inject into a browser workspace and no longer lives as an uncompressed JSONL file under GitHub Pages. Canonical bulk payloads remain in immutable Release shards.

During the Pages build, `scripts/prepare_pages_data.py` streams the canonical corpus against the static record index and emits bounded same-origin working sets:

- the complete-corpus Quasar entrypoint loads `/quasar-documents.json`;
- a named target or topic loads `/<dataset>/quasar-documents.json`;
- surface working sets are selected from the generated browser preview so graph-eligible records are preferred;
- the root working set defaults to 2,000 graph-eligible documents;
- named surfaces default to 500 full documents each;
- the records are exact canonical StarIntel documents, not reconstructed metadata objects.

The same pass hydrates compact record-index rows with bounded summaries for graph/entity record types. Bulk observation payloads remain metadata-only in the browser index so the Pages artifact stays bounded.

Generated dataset graph pages redirect to `quasar/index.html?dataset=<dataset>`. The root graph page redirects with `dataset=complete-corpus` when present.

## Router entrypoint

The embedded iframe starts at `quasar/app/`, not `quasar/app/index.html`. Quasar uses a `BrowserRouter` with `/quasar/app` as its basename, so the directory URL starts on a valid application route. After the working set loads successfully, the host bridge navigates to `/graph`.

## Pinned build

`quasar-fork.lock.json` records two exact revisions despite retaining its historical filename:

- `quasar_commit`: the `lost-rob0t/quasar` runtime and frontend-overlay commit.
- `quasar_ui_commit`: the `frontend/` submodule revision expected by that Quasar commit.

The Pages workflow checks out Quasar recursively, verifies both revisions, prepares the frontend overlays, validates and builds the frontend with `/quasar/app/` as its base path, generates AutoDig, hydrates bounded Pages data, and replaces the legacy graph entrypoints.

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

nimble buildFast
bin/starintel-site \
  --input digs \
  --db db \
  --output _site \
  --org-output .generated/org \
  --bulk-output .generated/bulk \
  --bulk-base-url https://example.invalid/bulk
python3 scripts/externalize_search_indexes.py --site _site --transport pages-static
python3 scripts/prepare_pages_data.py --site _site --bulk .generated/bulk

python3 scripts/build-auto-dig-quasar.py \
  --auto-dig-root . \
  --site-dir _site \
  --quasar-dist .quasar/frontend/dist \
  --quasar-commit "$quasar_commit" \
  --quasar-ui-commit "$quasar_ui_commit"
```

Open any generated dataset's `graph.html`. It transfers to the Quasar graph editor with that dataset's bounded canonical working set populated in Quasar's local corpus.
