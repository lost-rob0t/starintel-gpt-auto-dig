---
name: validate-starintel-changes
description: Run the mandatory StarIntel merge gate and prohibit merging invalid schema or DB changes.
---

# Validate StarIntel Changes

## Required command

Run this before marking a pull request ready, approving it, enabling auto-merge, or merging:

```bash
python3 scripts/validate-for-merge.py --site
```

Do not substitute a partial check.

## What the gate verifies

- Python compilation;
- the complete unit-test suite;
- exact reproducibility of `schemas/starintel-doc-v0.9.0.schema.json` from `starintel_doc/`;
- strict v0.9.0 validation of every normalized DB record and every packet record;
- `db/<dtype>/<_id>.ndjson` path consistency;
- exactly one compact JSON object and one terminating newline per normalized record;
- duplicate normalized IDs;
- relation endpoint integrity;
- complete site generation;
- `git diff --check` when running inside a Git checkout.

## Merge rule

A StarIntel document PR is mergeable only when:

1. `python3 scripts/validate-for-merge.py --site` exits with status 0;
2. every required GitHub check on the current head commit succeeds;
3. no check is pending, skipped, cancelled, unavailable, stale, or inconclusive;
4. the pull request head has not changed since validation.

If any condition is false, keep the pull request in draft and do not merge.

## Failure handling

When the gate fails:

1. identify the exact file, record, schema path, relation endpoint, or generated artifact reported by the validator;
2. fix or remove the invalid change;
3. rerun the complete gate from the repository root;
4. confirm GitHub checks against the new head commit;
5. merge only after everything is green.

Never:

- merge invalid documents and promise a later fix;
- bypass or edit around the validator;
- weaken schema constraints merely to admit bad data;
- hide ordinary typed metadata in `extensions` to evade a dtype schema;
- treat a skipped or unavailable check as success;
- merge based on validation from an older commit.
