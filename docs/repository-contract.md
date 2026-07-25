# Repository contract

## Canonical paths

```text
digs/<target>/<YYYY-MM-DD>-<loop-slug>/
db/<dtype>/<_id>.ndjson
roam/research/<project>/<node>.org
roam/indexes/<project>/<index>.org
manifests/<dataset>.json
reports/<dataset>.md
```

## Research transaction

A research publication is one logical transaction containing the applicable combination of:

1. packet-oriented or normalized StarIntel records;
2. a manifest with counts and hashes when using the normalized database form;
3. a readable report or packet README;
4. optional Org research and index nodes;
5. validation results.

The Git commit is the durable transaction boundary.

## Filename policy

The requested filename for normalized records is the literal StarIntel `_id`. Colons are therefore retained, for example:

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

## Publishing

The canonical publication workflow is the Python site generator on `main`:

```bash
python3 scripts/build_research_site.py \
  --input digs \
  --output _site \
  --org-output .generated/org
```

The workflow validates generated HTML, graph output, source indexes, and canonical JSONL downloads before GitHub Pages deployment. Org files may remain as durable research notes, but the repository does not use an Emacs-based Pages workflow.
