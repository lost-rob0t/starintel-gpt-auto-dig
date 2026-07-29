# Canonical DB search and link tooling

Use these scripts before adding a relation to an AutoDig packet. They resolve existing
StarIntel records, prefer normalized `db/` copies over packet duplicates, and fail on
ambiguous matches instead of guessing.

## Search and resolve

```bash
python3 scripts/search-db-links.py search 'Larry Fink' --dataset wef
python3 scripts/search-db-links.py resolve 'World Economic Forum'
python3 scripts/search-db-links.py neighbors 'Peter Thiel' --direction both
```

Add `--db-only` when packet-only records must be excluded. Search output includes the
canonical `_id`, dtype, dataset, source surface, repository path, and match reason.

## Emit a validated relation draft

```bash
python3 scripts/create-db-link.py \
  'Larry Fink' \
  co_chairs \
  'World Economic Forum' \
  --dataset wef \
  --confidence 0.99 \
  --source-id starintel:source:wef-laurence-fink-board-profile \
  --output .work/fink-wef-relation.jsonl
```

The link script resolves endpoints from normalized `db/` records by default. Use
`--include-packets` only when creating a packet-local relation that will not be
imported into `db/` until its endpoints are normalized.

The script:

1. resolves both endpoints against the canonical corpus;
2. rejects missing or ambiguous endpoints;
3. creates a schema-valid StarIntel v0.9.0 `relation`;
4. refuses to write directly into `db/`.

Review the draft, then import it through the required transactional path:

```bash
python3 scripts/starintel.py import .work/fink-wef-relation.jsonl
python3 scripts/validate-for-merge.py --site
```
