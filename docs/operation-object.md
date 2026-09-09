# StarIntel `operation` control-plane object

Tracking design: [`lost-rob0t/starintel-server#151`](https://github.com/lost-rob0t/starintel-server/issues/151).

`operation` is a first-class control-plane document above `target` and `investigation-target`. It is **not** a real-world intelligence entity. It represents executable knowledge about why a body of work exists, which phases are runnable, what dependencies and scope apply, which datasets and capabilities may be used, and what should happen after termination.

## Relationship to targets

- `target`: identifies work to perform.
- `investigation-target`: identifies a bounded investigative question to resolve.
- `operation`: coordinates targets and investigative targets across a phased mission.

Operations reference targets; they do not replace or collapse the target dtypes.

## Phases

`data.phases` is a dependency DAG. Each phase has a stable `phase_id`, objective, state, dependencies, optional entry/exit conditions, local scope, target policy, target references, dataset bindings, capability requirements, deliverables, and completion evidence.

Operation-level `out_of_scope` is authoritative over phase-local `in_scope`. The validator rejects an exact contradictory scope item instead of allowing a child phase to loosen mission scope.

Current phase states are:

`planned`, `ready`, `active`, `blocked`, `awaiting-review`, `completed`, `skipped`, `failed`, `aborted`.

The validator rejects missing phase references, self-dependencies, dependency cycles, and completed phases without completion evidence.

## Datasets

Operations bind multiple datasets with stable binding IDs. A binding records the dataset, its operation role, permitted access mode, applicable phases, and purpose. Phases reference bindings by ID so an agent can determine which data surfaces it may touch in the current phase.

## Capability gaps

`data.capability_gaps` makes R&D and tooling needs explicit. Categories include actor, software, hardware, device, source, dataset, schema, protocol, infrastructure, and research. A capability can be blocking and can point to the phase(s) that require it and to a later resolution artifact.

This is intended to support a future loop in which an unavailable blocking capability creates or links R&D/design work and the dependent phase becomes runnable only after resolution.

## Post-operation actions

`data.post_actions` describes structured terminal/follow-up work such as report generation, archival, promotion of findings, follow-up targets/operations, scheduled revisits, exports, capability evaluation, coverage evaluation, and provenance preservation. `action_type` remains an extensible string in the initial v0.9 slice.

## Agentic semantics

The structured representation is designed to support symbolic queries equivalent to:

```prolog
currentPhase(Operation, Phase).
phaseRunnable(Operation, Phase).
phaseBlockedBy(Operation, Phase, Dependency).
validTarget(Operation, Phase, Target).
allowedDataset(Operation, Phase, Dataset, Access).
phaseComplete(Operation, Phase).
nextPhase(Operation, Current, Next).
operationComplete(Operation).
capabilityMissing(Operation, Phase, Capability).
```

The initial schema does **not** define those language-specific APIs. It preserves the information needed to implement them without changing the document shape.

## JSON-LD ontology re-examination gate

The Python v0.9 registration in `starintel_doc/operation_spec.py` is transitional compatibility with the current executable schema. It is not the permanent semantic authority.

Before the operation vocabulary is treated as final, re-examine it under the canonical StarIntel JSON-LD ontology system and answer at least:

1. whether `Operation` is an ontology class, a control-plane profile, or both;
2. how `Operation`, `Phase`, `Target`, `InvestigationTarget`, `Dataset`, `Capability`, agents/actors, deliverables, and evidence are linked;
3. which relations reuse established provenance/activity semantics and which require StarIntel-native terms;
4. how state vocabularies and custom operation ontologies are extended/versioned without per-language source changes;
5. which constraints belong to ontology semantics versus structural/runtime validation.

No Python, Common Lisp, Nim, JavaScript, or Prolog implementation should become the semantic authority once the JSON-LD ontology loader is in place.
