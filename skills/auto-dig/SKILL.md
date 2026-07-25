---
name: auto-dig
description: Run a complete schema-enforced StarIntel research loop from search through document creation, validation, and recursive target selection.
---

# StarIntel Auto Dig

## Loop

1. Search existing records with `search-starintel-json-db`.
2. Define the research question and root target.
3. Collect sources and evidence.
4. Create typed documents with `create-starintel-documents`.
5. Validate the packet and normalized DB.
6. Select recursive targets with `select-recursive-targets`.
7. Append a `research-pass` document containing method, findings, support IDs, counterevidence IDs, unresolved target IDs, agent identity, iteration, and completion time.
8. Publish through the repository branch workflow.

## Required commands

```bash
python3 -m compileall -q starintel_doc scripts
python3 -m unittest discover -s tests -v
python3 scripts/validate-db.py
python3 scripts/build_research_site.py --input digs --db db --output _site --org-output .generated/org
```

## Schema discipline

The loop may create only documents accepted by `starintel_doc.validate_document`. It may not emit an approximate “StarIntel-like” object and repair it later. When a source exposes a useful field absent from the registry, preserve it under a namespaced extension and open a schema change before using that field as a normal output field.
