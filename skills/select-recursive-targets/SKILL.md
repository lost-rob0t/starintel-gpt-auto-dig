---
name: select-recursive-targets
description: Rank entities and emit schema-valid investigation-target documents for recursive StarIntel auto-dig passes.
---

# Select Recursive Dig Targets

## Command

```bash
python3 scripts/starintel.py select-targets \
  --query '<current subject>' \
  --limit 20 \
  --depth 1 \
  --max-depth 3 \
  --root-target-id <root-id> \
  --output-dataset <dataset> \
  --emit-documents \
  --output recursive-targets.jsonl
```

## Ranking model

The deterministic selector scores:

- dtype relevance;
- graph degree and references from found records;
- assessment relevance, priority, threat, impact, and confidence;
- source and evidence coverage;
- unresolved gaps and verification items;
- prior target selection, which is excluded to prevent duplicate loops.

## Procedure

1. Search the corpus for the current pass or feed the selector the scoped corpus.
2. Exclude existing `target` and `investigation-target` identities.
3. Rank candidates.
4. Inspect the score reasons and seed IDs.
5. Emit `investigation-target` documents.
6. Import accepted targets:

```bash
python3 scripts/starintel.py import recursive-targets.jsonl --replace
```

7. Start the next dig from the highest-ranked target while preserving `root_target_id`, recursion depth, seed IDs, and selection reasons.
8. Stop at `max_depth` or when no candidate clears the operator’s threshold.

The selector proposes research order. It does not convert association, graph centrality, or threat metadata into guilt or factual conclusions.
