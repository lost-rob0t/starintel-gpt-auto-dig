# Auto-Dig request #2576 — Dallas booking-charge follow-up

Worker 8/8 bounded additive follow-up for issue #2576.

## Scope

This pass reuses the canonical event `starintel:event:dallas-march-on-rnc-midterm-convention-2026-09-10` and the already-merged event-outcome packet. It does **not** create a competing event identity or person dossier.

A September 12 WBAP report, mirroring reporting from The Dallas Express and explicitly citing Dallas County jail records, narrows the prior booking-charge gap. It reports that the two people booked after the September 10 protest carried these charge sets:

- one booking: two counts of assault causing bodily injury plus one count of obstructing a highway or passageway;
- the other booking: one count of assault causing bodily injury, one count of interference with public duties, and one count of obstructing a highway or passageway;
- each individual had three reported $5,000 bonds, or $15,000 total bond per person.

These remain **charges/accusations, not findings of guilt**. The packet intentionally does not infer political affiliation, organizational membership, or broader intent from attendance or arrest.

## Remaining gaps

- native Dallas County jail/booking records and identifiers;
- native Dallas Police incident/arrest reports and case numbers;
- later charging amendments, dismissals, pleas, trial outcomes, or other dispositions;
- native OSE permit application/cancellation email and route attachments;
- final DPD-facilitated route/traffic-control plan;
- official after-action report or official crowd estimate.

## Materialization

`starintel-documents.jsonl` is the authored packet. Normalized `db/` records must be generated only through the canonical importer:

```sh
python3 scripts/schema-release.py current
python3 scripts/schema-release.py check
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype source
python3 scripts/starintel.py schema --dtype analysis
python3 scripts/starintel.py schema --dtype research-pass
python3 scripts/starintel.py import digs/dallas/2026-09-15-request-2576-booking-charge-followup/starintel-documents.jsonl
```

Do not hand-edit normalized `db/` records.
