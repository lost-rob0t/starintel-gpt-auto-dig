# Auto-Dig agents

This directory contains durable agent policy and state contracts used by automated Auto-Dig workers.

## `auto-dig-prolog`

`auto_dig_prolog_actor.pl` is the first supervised Prolog-RLM-backed Auto-Dig actor.

The control split is intentional:

```text
GitHub Actions
  -> snapshots queue + durable state
  -> starts pinned prolog-rlm runtime
  -> Prolog actor selects one eligible request
  -> depth-1 RLM reasons over the selected request
  -> successful run is pushed to its own branch
  -> durable state advances only after push
```

GitHub Actions owns credentials, checkout, repository mutation, logs, scheduling, and branch push. Prolog owns queue-selection semantics and actor execution. Prolog-RLM owns bounded recursive reasoning and traces.

### Branch convention

Every run pushes to:

```text
<agent-name>/<YYYY-MM-DD>-<run-id>
```

For this actor:

```text
auto-dig-prolog/2026-08-24-123456789-1
```

The GitHub run id and attempt form the run id so reruns never collide with the first attempt.

### Repeat policy

The queue selector implements the current Auto-Dig recurrence rule:

- `high` and `urgent` targets may be selected again on consecutive runs;
- `normal` and `low` targets may not be selected twice in a row;
- when the only remaining candidate would violate that rule, the actor idles instead of silently repeating it.

### Durable state

State is stored in the body of the repository issue titled:

```text
[actor-state] auto-dig-prolog
```

The body is raw JSON following `auto_dig_prolog_state.schema.json`.

State is not advanced when selection, Prolog-RLM execution, commit, or branch push fails. A failed run therefore remains recoverable/retryable instead of being recorded as consumed work.

### Current execution stage

The initial workflow intentionally stops after a bounded live RLM reasoning pass. It does not pretend that a plan is completed research. The run branch contains:

- selected request snapshot;
- actor decision;
- supervised actor trace;
- portable Prolog-RLM trace;
- RLM result;
- run manifest.

The next stage is to bind read-only web/MCP research tools and canonical StarIntel write/validation operations behind the same capability/authority boundaries.

### Prolog-RLM bug harvesting

The workflow exercises a pinned real Prolog-RLM checkout. Failures preserve diagnostics as GitHub Actions artifacts. If the optional `PROLOG_RLM_BUG_TOKEN` repository secret is configured, a failed run also opens a cross-repository integration issue in `lost-rob0t/prolog-rlm` with the pinned runtime SHA and workflow reproduction link.

The bug filer deliberately does not call every consumer failure a core bug: the issue instructs triage to distinguish Prolog-RLM defects from Auto-Dig configuration/integration failures.
