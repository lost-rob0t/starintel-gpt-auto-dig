# Auto-Dig request queue

Auto-Dig research requests live in GitHub Issues, not Discussions. Issues are the better queue primitive because they have an explicit open/closed lifecycle, searchable labels, comments for machine receipts, and a terminal completed state.

The shared queue is every open issue labeled `investigation-target`. The generic issue form is `.github/ISSUE_TEMPLATE/auto-dig-request.yml`; existing domain-specific forms such as Flock locality investigations remain first-class queue entries.

## Request format

A generic request contains:

- **Subject**: the person, organization, event, system, claim, dataset, or relationship to investigate.
- **Goal**: the concrete question or result the dig should answer.
- **Scope**: required surfaces, jurisdictions, dates, entities, recursion requirements, or exclusions.
- **Seed sources**: optional URLs, filings, document IDs, existing StarIntel records, names, or claims.
- **Constraints**: optional limits beyond repository policy.
- **Priority**: `urgent`, `high`, `normal`, or `low`.
- **Completion criteria**: what must exist before the issue can close.
- **Stable dedupe key**: optional operator-supplied identity for requests that should remain equivalent even when reworded.

Requests created from the Actions tab use `.github/workflows/auto-dig-request.yml`. That workflow renders the same format with `scripts/auto_dig_request.py`, computes a stable request fingerprint, searches all existing issues for that fingerprint, and creates a new issue only when no equivalent request already exists.

## Hourly GPT queue semantics

Every hourly GPT Auto-Dig run follows this order:

1. Read `AGENTS.md` and the applicable repository instructions.
2. Query all open `investigation-target` issues.
3. Rank explicit generic requests by `urgent`, `high`, `normal`, then `low`; preserve oldest-first order within the same priority. Domain-specific request issues without a priority field are `normal`.
4. Drain the request queue before autonomous research. Process as many eligible requests as the run can complete without skipping validation, merge, publication, or evidence requirements.
5. A run may leave requests open only when it hits a real runtime/tool boundary, required evidence is unavailable, validation fails, or a request is blocked by a stated constraint. It must not stop after one request merely because one request completed.
6. Only when no eligible open request remains may the runner select autonomous work from the free-range frontier.
7. Autonomous fallback uses the existing `free-range-auto-dig` workflow and repository target selector. It does not create synthetic request issues simply to keep itself busy.

## Idempotency and deduplication

Queue retries must be safe.

### Request identity

Action-created requests carry a visible `Request key: auto-dig:<fingerprint>` line. The fingerprint is derived from normalized subject, goal, scope, and completion criteria unless an operator supplies a stable dedupe key.

The GitHub Action searches both open and closed issues for the fingerprint. Re-running the action with an equivalent request returns the existing issue instead of creating a duplicate.

Issue-form requests that do not already carry an action-generated fingerprint are still stable by GitHub issue number. The hourly runner may compute the same v1 fingerprint from the form fields when useful, but it must never rewrite evidence or invent a new issue solely to attach a fingerprint.

### Output identity

Before writing research for issue `#N`, the hourly runner must search the repository and recent commit history for the issue URL, `Auto-Dig request #N`, existing canonical StarIntel IDs, and any already-materialized packet covering the same request.

If the requested result is already present and valid, the runner does not create another packet or duplicate normalized records. It validates the existing result, posts the completion receipt, and closes the issue.

If new evidence materially updates an existing canonical record, use the repository's normal stable-ID/version/correction rules. A retry is never justification for a second identity.

Packet directories should be deterministic for the request when a new packet is required, using the canonical subject root and an issue-qualified slug such as `digs/<canonical-root>/<YYYY-MM-DD>-request-<N>-<slug>/`. Re-runs update or reuse that packet rather than minting sibling copies for the same request.

Every normalized database write still goes through the scripted StarIntel write/import path in `AGENTS.md`. Queue machinery does not weaken schema, provenance, or validation rules.

## Completion and issue closure

A request closes only after the research changes are merged and the relevant Auto-Dig data is published or otherwise available on the canonical public surface.

The final GPT issue reply contains:

```markdown
## Auto-Dig complete

### Findings
- Concise finding with evidence status.
- Concise finding with evidence status.
- Remaining uncertainty, if any.

### Changes
- Commit: <canonical GitHub commit URL>
- Commit: <canonical GitHub commit URL>

### Auto-Dig data
- <exact relevant https://auto-dig.starintel.actor/... URL>
- StarIntel IDs: `<id>`, `<id>`

### Validation
- `<validation command>`: passed
- Publication/site check: passed

Request identity: `#N` / `auto-dig:<fingerprint when present>`
```

Do not fabricate a deep Auto-Dig URL. If an item-specific route cannot be verified, link the closest verified dataset or search surface and include the exact StarIntel IDs needed to locate the records.

After posting that receipt, close the issue as completed. If validation, merge, or publication is not complete, leave the issue open and post the concrete blocker instead.
