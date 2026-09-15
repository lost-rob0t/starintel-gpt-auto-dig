# Auto-Dig request #2576 — Dallas protest logistics/outcome

Worker 8/8 bounded pass for issue #2576.

## Scope

This pass **reuses** the existing canonical event `starintel:event:dallas-march-on-rnc-midterm-convention-2026-09-10`; it does not create a competing event identity.

It adds public source-backed evidence that:

- the City of Dallas Office of Special Events is the city authority for outdoor temporary-activity permits under Chapter 42A;
- Dallas Police described its First Amendment Activity form as an informational/coordination mechanism distinct from a special-event permit;
- the already-canonical September 10 march proceeded after the permit dispute; and
- NBC 5 reported Dallas Police said two protesters were arrested near McKinnon and Payne, one accused of assaulting a counter-protester and one accused of obstructing a road.

Arrest descriptions remain allegation/arrest state only. This packet does not assert guilt or final charges and does not collect unrelated personal information.

## Remaining gaps

- native OSE permit application, cancellation email, route attachments, and City/DPD correspondence;
- any final DPD-facilitated route or traffic-control plan;
- native incident/arrest reports, booking charges, case numbers, and later dispositions;
- official after-action report or official crowd estimate.

## Materialization

`starintel-documents.jsonl` is the authored packet. Normalized `db/` records must be generated through the canonical importer:

```sh
python3 scripts/schema-release.py current
python3 scripts/schema-release.py check
python3 scripts/starintel.py import digs/dallas/2026-09-15-request-2576-dallas-event-outcome/starintel-documents.jsonl
```

Do not hand-edit the normalized `db/` records.
