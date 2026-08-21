# Flock Safety: Columbus audit-surface opacity recursion

Generated: `2026-07-31T02:40:00-04:00`

This is the fourth recursive pass over the Columbus Flock graph. It follows directed sharing into the audit system that is supposed to prove who actually used those edges.

## Result

Flock auditability is split across two views:

- **Organization Audit**: actions by an agency's own users.
- **Network Audit**: searches on a camera-owning agency's network by its own users and users at agencies it shares with.

In December 2025, Flock announced that Network Audits would retain the searching agency, date, offense type, and a unique search identifier while removing officer name, specific plate, vehicle fingerprint, and open-text reason.

That creates a **split-custodian reconstruction problem**. The camera owner sees that a search occurred but loses the fields needed to attribute the operator and inspect the exact target and stated purpose. The searching agency may retain richer Organization Audit data. A complete investigation therefore requires records from both sides, joined through the retained search identifier and interpreted against the product schema in force at the time.

## Core finding

```text
searching agency Organization Audit
        + stable unique search ID
camera-owner Network Audit
        + product/export schema version
sharing configuration + policy version
        = reconstructable search event
```

Without the cross-surface join, a camera owner cannot independently answer **who searched what and why** from its reduced Network Audit alone.

## Counts

- analysis: 3
- claim: 5
- dataset-manifest: 1
- event: 4
- investigation-target: 11
- org: 7
- person: 4
- policy: 3
- relation: 9
- research-pass: 1
- source: 9
- total: **57**

## Evidence boundaries

- Flock's December 9 email is a vendor communication released through public records.
- Removal of fields from one export does not prove the underlying internal records were deleted.
- A unique search identifier is only useful if it appears consistently across Organization and Network Audits and remains stable through exports.
- Have I Been Flocked's operator-name resolution is probabilistic and explicitly requires official verification for certainty.
- Public portal records are not treated as equivalent to native Organization Audit or Network Audit exports.
- The Columbus MuckRock request remains listed as awaiting response in the reviewed page; no production is inferred.

## Next recursion

1. Recover CPD Organization Audit exports.
2. Recover CPD Network Audit exports.
3. Test unique-search-ID joins across both surfaces.
4. Reconstruct field/schema changes by product version and date.
5. Recover CPD user, role, and administrator history.
6. Capture the native CPD portal schema and API responses.
7. Audit offense-type, reason-code, and case-number quality.
8. Resolve Columbus PRR #25-7576 and related productions.
9. Independently reproduce the July 2026 CPD audit.
10. Implement a cross-surface reconciliation actor.

## Validation

- JSONL parse: passed
- unique IDs: passed
- relation endpoints: passed
- target seed references: passed
- transport SHA-256: `08183396e741d2e952c0bafc8d0a8b5153b2e84b1039b88284bc9d63dcde640b`
- StarIntel schema and repository CI: pending
