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
  -> Prolog expert KB selects model + reasoning effort
  -> depth-1 RLM reasons over the selected request using that enforced route
  -> successful run is pushed to its own branch
  -> durable state advances only after push
```

GitHub Actions owns credentials, checkout, repository mutation, logs, scheduling, and branch push. Prolog owns queue-selection semantics, actor execution, and model-routing policy. Prolog-RLM owns bounded recursive reasoning, provider requests, reasoning-effort enforcement, and traces.

### Expert model routing

`auto_dig_model_router.pl` is the routing knowledge base. Workflow configuration does not choose the normal research model.

The current policy is deliberately cost-aware:

- bulk classification/extraction/normalization work starts on Luna at `high`;
- ordinary research, verification, coding, and recursive worker tasks default to Luna at `max`;
- one failed verification escalates to Terra at `max`;
- two failed verifications, critical/irreversible work, threat models, security adjudication, publication gates, and final adjudication route to Sol at `max`.

A route contains both the provider model identifier and `reasoning.effort`. The workflow passes both to Prolog-RLM. An explicit host-selected reasoning effort therefore applies to direct requests and nested model steps; model-generated plan options cannot silently downgrade it. A separate trusted planner override remains available in Prolog-RLM when a caller intentionally needs one.

Every live run persists both:

```text
model-profile.json
model-route.json
```

alongside the runtime trace so a routing decision is inspectable after the fact.

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

State is not advanced when selection, model routing, Prolog-RLM execution, commit, or branch push fails. A failed run therefore remains recoverable/retryable instead of being recorded as consumed work.

### Current execution stage

The initial workflow intentionally stops after a bounded live RLM reasoning pass. It does not pretend that a plan is completed research. The run branch contains:

- selected request snapshot;
- actor decision;
- supervised actor trace;
- model-routing profile and decision;
- portable Prolog-RLM trace;
- RLM result;
- run manifest.

The next stage is to bind read-only web/MCP research tools and canonical StarIntel write/validation operations behind the same capability/authority boundaries.

### Prolog-RLM bug harvesting

The workflow exercises a pinned real Prolog-RLM checkout. Failures preserve diagnostics as GitHub Actions artifacts. If the optional `PROLOG_RLM_BUG_TOKEN` repository secret is configured, a failed run also opens a cross-repository integration issue in `lost-rob0t/prolog-rlm` with the pinned runtime SHA and workflow reproduction link.

The bug filer deliberately does not call every consumer failure a core bug: the issue instructs triage to distinguish Prolog-RLM defects from Auto-Dig configuration/integration failures.
