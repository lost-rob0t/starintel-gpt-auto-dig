# Auto-Dig request #2575 — Dallas protest permit / DPD coordination

Worker 7/8 bounded pass for issue #2575.

## Scope

This pass reuses the existing canonical September 10 Dallas march event and Dallas Against the Trump Agenda Coalition organization. It does not create duplicate event or organization identities.

It advances the issue by:

- identifying the **Dallas Observer, September 2, 2026** article as the strongest local-media match for the second-hand permit/coordination claim;
- preserving the Observer's reporting that the Office of Special Events canceled the special-event permit application at DPD's request and that DPD preferred direct coordination as a quicker path;
- preserving separate reporting identifying **Allison Hudson**, Dallas Police assistant director for media relations/community affairs, and the permit-associated organizer-cost rationale;
- joining the current City of Dallas Office of Special Events fee schedule, which establishes ordinary permitted-activity public-safety cost categories; and
- distinguishing **permit cancellation / bypass** from a **formal fee waiver**.

## Evidence boundary

The evidence substantially corroborates the core process claim: Dallas PD/OSE moved the organizers away from the special-event permit path and toward direct DPD coordination, with permit-associated public-safety costs part of the explanation.

This pass does **not** claim that:

- an already-issued permit was formally waived;
- the coalition received any particular dollar-value subsidy or waiver;
- the convention-wide city security budget was a protest-organizer cost;
- a final city-approved route, traffic-control plan, staffing plan, invoice, or zero-balance statement has been recovered; or
- administrative coordination implies ideological affiliation.

The native Office of Special Events cancellation email/application file, final DPD coordination records, route/traffic-control materials, and billing/waiver records remain unresolved.

## Canonical records

The packet contains three v0.9.0 records:

- 1 `source`
- 1 `analysis`
- 1 `research-pass`

The merged #2576 KERA source is reused rather than duplicated.

Normalized `db/` records must be produced only through:

```bash
python3 scripts/starintel.py import \
  digs/dallas/2026-09-15-request-2575-dallas-permit-coordination/starintel-documents.jsonl
```

## Merge gate

Do not merge until the temporary materializer has removed itself and the exact-head required workflows are green, including `Validate StarIntel documents` with `Run complete canonical merge gate` and the full Auto-Dig site/ADAR surface gate.

Issue #2575 should remain open after this pass for the native cancellation/application file, final coordination/route/traffic plan, and billing/waiver proof.
