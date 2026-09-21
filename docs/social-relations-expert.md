# Social Relations Expert

The social-relations lane turns existing StarIntel relation documents into an
explainable symbolic graph without pretending that graph proximity is proof.

## What was reused from Auto-Dig

The implementation follows the current Auto-Dig patterns rather than adding a
parallel data model:

- canonical packets remain `starintel-documents.jsonl`;
- every relation keeps StarIntel `_id`, dataset, typed predicate, confidence,
  sources, evidence, handling, and provenance;
- investigation gaps become `investigation-target` records;
- the repository control file is checked before live research;
- live corpus access stays read-only through the existing StarIntel corpus MCP;
- canonical ingest remains a separate capability through
  `scripts/import-starintel-documents.py`.

## Reasoning layers

### Explicit evidence aggregation

`relation_assessment/3` aggregates source-backed relation records for a pair.
It measures:

- predicate-specific evidentiary weight;
- confidence from the original relation records;
- number of independent source keys;
- multiplexity (distinct relation predicates);
- directional reciprocity;
- exact supporting StarIntel relation IDs.

The score is an assessment of the **available relation evidence**, not a claim
about friendship, intent, trust, ideology, or private behavior.

### Derived association candidates

`association_candidate/4` is deliberately narrower. It requires at least two
shared non-sensitive contexts and emits only the generic
`associated_with` concept. Derived confidence is capped at 0.72 and the
candidate is always marked `requires_review`.

Membership alone is not used for shared-context derivation because an
organization can itself encode political, religious, or union affiliation.

### Bridge detection

`bridge_candidate/4` identifies a node with independently evidenced ties to
two nodes that do not have an evidenced direct tie. This is useful for graph
navigation and research prioritization; it is not an assertion that the bridge
caused communication between the other nodes.

### Follow-up generation

Weak or derived ties can produce a bounded follow-up object via
`suggested_followup/3`. The follow-up asks for direct public evidence and
independent corroboration while explicitly excluding identity guessing,
sensitive-trait inference, and private contact collection.

## Example

```prolog
?- use_module(agents/social_relations_expert).
?- load_starintel_jsonl('scratch/social-slice.jsonl').
?- relation_assessment('starintel:person:a',
                       'starintel:org:x',
                       Assessment).
?- association_candidate('starintel:person:a',
                         Other,
                         Score,
                         Reasons).
```

The expert owns no database and no write token. OpenCode can use its output to
prepare proposed StarIntel records; review/validation and ingest stay separate.
