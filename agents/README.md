# Auto-Dig agents

This directory contains durable agent policy and state contracts used by automated Auto-Dig workers.

## `auto-dig-prolog`

`auto_dig_prolog_actor.pl` is the supervised Prolog-RLM-backed Auto-Dig actor.

The control split is intentional:

```text
GitHub Actions
  -> snapshots queue + durable state
  -> starts exact-pinned prolog-rlm runtime
  -> Prolog actor selects one eligible request
  -> Prolog expert KB selects model + reasoning effort
  -> native Prolog-RLM typed planner reasons over the selected request
     with automatic default skills, compiled prompt projection,
     bounded context search/peek/slice, and depth-2 recursion
  -> successful run is pushed to its own branch
  -> durable state advances only after push
```

GitHub Actions owns credentials, checkout, repository mutation, logs, scheduling, and branch push. Prolog owns queue-selection semantics, actor execution, and model-routing policy. Prolog-RLM owns bounded recursive reasoning, provider requests, reasoning-effort enforcement, prompt compilation, skill activation, child-result acceptance, context projection, budgets, and traces.

### Prolog-RLM integration contract

`auto_dig_rlm_runner.pl` deliberately uses the public `rlm_completion/4` runtime instead of the convenience `prolog-rlm rlm` CLI. The convenience CLI currently supplies a fixed planner and disables skills for its small deterministic RLM lane; that is the wrong contract for Auto-Dig research.

The Auto-Dig runner explicitly enables or relies on the current native runtime path:

- `skill_mode(on)` with the default `rlm-operate`, `rlm-recurse`, `rlm-facts`, and `rlm-constraints` operating skills;
- `prompt_compile_mode(compiled)` so the symbolic prompt compiler owns provider-visible projection;
- the native typed root planner, with bounded validation retries instead of a host-injected fixed plan;
- `context(slice)`, `context(search)`, and `context(peek)`;
- bounded depth-2 recursion and model/context-operation ceilings;
- permanent operating context propagation to nested/retry model calls supplied by current Prolog-RLM;
- current proof-carrying child-result acceptance and delegation boundaries supplied by Prolog-RLM.

`test_auto_dig_rlm_runner.pl` locks the parts of this integration contract that Auto-Dig controls directly and fails if the runner silently returns to the fixed-planner/skills-off path.

The workflow pins an exact Prolog-RLM commit and verifies the checkout SHA before running anything. A pin update is therefore an explicit compatibility change, not a floating dependency.

### Running investigation target #2297

Issue `#2297` is an `investigation-target` and can be selected normally by the scheduled actor. To force that target for a manual run, dispatch the `Auto-Dig Prolog actor` workflow with:

```text
force_issue = 2297
```

Equivalent GitHub CLI invocation:

```bash
gh workflow run auto-dig-prolog-actor.yml \
  -R lost-rob0t/starintel-gpt-auto-dig \
  -f force_issue=2297
```

The forced issue still passes through the same supervised actor, expert model route, budgets, RLM feature contract, branch isolation, and durable-state gates.

### GitHub secrets

The actor has one required custom secret and one optional integration-reporting secret:

- `OPENROUTER_API_KEY` — **required** for the live Prolog-RLM reasoning step. This is the OpenRouter API key used by the expert-selected model route.
- `PROLOG_RLM_BUG_TOKEN` — **optional**. When present, a failed Auto-Dig actor run can open a reproducible integration issue in `lost-rob0t/prolog-rlm`. A fine-grained PAT only needs access to `lost-rob0t/prolog-rlm` with **Issues: Read and write**; normal metadata read access is implicit.

Do **not** create a `GITHUB_TOKEN` secret. GitHub injects `${{ github.token }}` automatically. This workflow scopes that built-in token with `contents: write` and `issues: write` for Auto-Dig branch/state/receipt operations.

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
auto-dig-prolog/2026-08-27-123456789-1
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

The workflow still stops after a bounded live RLM reasoning pass. It does not pretend that a plan is completed research. The run branch contains:

- selected request snapshot;
- actor decision;
- supervised actor trace;
- model-routing profile and decision;
- portable Prolog-RLM trace;
- RLM result;
- run manifest, including the enabled RLM feature contract.

Read-only web/MCP research tools and canonical StarIntel write/validation operations remain a separate capability/authority gate. They should be bound without weakening the current Prolog-RLM planning, skill, context, or authority boundaries.

### Prolog-RLM bug harvesting

The workflow exercises a pinned real Prolog-RLM checkout. Failures preserve diagnostics as GitHub Actions artifacts. If the optional `PROLOG_RLM_BUG_TOKEN` repository secret is configured, a failed run also opens a cross-repository integration issue in `lost-rob0t/prolog-rlm` with the pinned runtime SHA and workflow reproduction link.

The bug filer deliberately does not call every consumer failure a core bug: the issue instructs triage to distinguish Prolog-RLM defects from Auto-Dig configuration/integration failures.
