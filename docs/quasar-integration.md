# Quasar inside Auto-Dig

Auto-Dig consumes the complete `lost-rob0t/auto-dig-quasar` application at an exact commit recorded in `quasar-fork.lock.json`. The fork is built with `/quasar/app/` as its Vite base path. `scripts/build-auto-dig-quasar.py` copies that artifact into the generated site and creates a controlled shell at `/quasar/`.

## Why an iframe

Auto-Dig currently generates a Python static site. Quasar is a React/Vite SPA with its own router and dependency graph. Direct mounting would require turning Auto-Dig into a JavaScript workspace or duplicating Quasar dependencies. The controlled same-origin iframe keeps both applications functional while preserving a narrow typed bridge.

The frame:

- validates exact origins and frame source;
- uses `auto-dig-quasar.v1` typed messages;
- never places tokens in URLs;
- does not permit top navigation;
- exposes only the documented bridge methods;
- stores document overlays, graphs, correction reports, and actor runs in local IndexedDB;
- keeps tips inside Quasar local storage;
- synchronizes theme, dataset, active run, route, and actor findings.

## Local build

```bash
# In auto-dig-quasar
npm ci
VITE_BASE_PATH=/quasar/app/ npm run build

# In starintel-gpt-auto-dig
python3 scripts/validate-for-merge.py --site
python3 scripts/build-auto-dig-quasar.py \
  --auto-dig-root . \
  --quasar-dist ../auto-dig-quasar/dist \
  --quasar-fork-commit "$(git -C ../auto-dig-quasar rev-parse HEAD)" \
  --quasar-upstream-commit "$(git -C ../auto-dig-quasar rev-parse upstream/main)"
python3 -m http.server 8000 --directory site
```

Open `http://localhost:8000/quasar/index.html?dataset=<target-directory>`.

## Local actor adapters

The host provides `auto-dig.local.investigation` without external services. A richer local runtime may register adapters before `host.js` handles requests:

```js
window.autoDigActorAdapters = {
  "actor.id": async (request) => ({ documents: await runLocalActor(request) })
};
```

Adapters receive only the typed request. They do not receive arbitrary Quasar state.

## Correction reports

Quasar strips private/local fields, persists the report locally, displays the exact payload, and opens a prefilled GitHub issue only after explicit confirmation. The browser never submits the issue automatically.

## Tipline

Tips are local by default. Users can create, triage, link, convert, run Auto-Dig, export, or delete them. A remote destination must be selected and confirmed before any future remote adapter receives content.
