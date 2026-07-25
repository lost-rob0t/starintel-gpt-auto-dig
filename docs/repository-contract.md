# Repository contract

## Canonical paths

```text
db/<dtype>/<_id>.ndjson
roam/research/<project>/<node>.org
roam/indexes/<project>/<index>.org
manifests/<dataset>.json
reports/<dataset>.md
```

## Research transaction

A research publication is one logical transaction containing:

1. normalized StarIntel records;
2. a manifest with counts and hashes;
3. a readable report;
4. Org-roam research and index nodes;
5. validation results.

The Git commit is the durable transaction boundary.

## Filename policy

The requested filename is the literal StarIntel `_id`. Colons are therefore retained, for example:

```text
db/org/starintel:org:palantir-technologies-inc.ndjson
```

This is valid in Git and on GitHub, but Windows filesystems cannot check out colon-containing names. Consumers on Windows should use sparse/API access or a path-mapping importer.

## Update policy

Records are immutable by identity but replaceable by correction or version:

- same `_id`, newer `version`: replace intentionally;
- same `_id`, same `version`, changed bytes: treat as a correction and document it in the commit;
- different `_id`: add a new file;
- deletions require a documented reason.

## Evidence policy

The repository records what a source supports. It does not treat:

- lobbying as corruption;
- former public employment as misconduct;
- a contract ceiling as paid revenue;
- an advocacy characterization as neutral fact;
- a corporate statement as independent verification.

## Org-roam publication

The publication workflow follows the same model as `starintel-auto-research`:

- isolated `emacs --batch -Q`;
- dependencies installed under `.cache/emacs`;
- staged copy of `roam/`;
- Org-roam database generated under `.cache/pages`;
- one HTML page per Org file;
- backlinks, search index and graph index;
- internal-link validation;
- GitHub Pages deployment from `main`.
