# Palantir graph connectivity and person rationale

## Scope

This pass repairs the disconnected nodes visible around the `1789 Capital`, executive-branch, `Executive Order 14243`, and Vulcan/OSC clusters.

The underlying records already contained many of the facts. The graph stayed fragmented because several facts were stored as metadata arrays (`executive_ids`, `owner_ids`, `participant_ids`, `issuer_id`, `affected_ids`) or as embedded relation endpoint objects instead of explicit string-ID relations.

## What changed

- Added explicit person-to-organization edges for Omeed Malik and Donald Trump Jr. at 1789 Capital.
- Added Chris Buskirk's explicit Rockbridge Network edge.
- Created a canonical Thiel Capital organization endpoint and repaired the Michael Kratsios and Peter Thiel links.
- Added OSTP and State Department endpoints so Kratsios and Jacob Helberg connect to the federal executive branch.
- Repaired Helberg's Palantir CEO-adviser relation using the canonical Alex Karp ID.
- Converted EO 14243's issuer and affected-branch metadata into explicit relations.
- Converted Vulcan/OSC event participation into explicit relations.
- Added Peter Navarro as a bounded, attributed process lead tied to the Vulcan review.

## Why each person is listed

| Person | Source-backed reason for inclusion | Evidence boundary |
|---|---|---|
| Chris Buskirk | Co-founder/CIO of 1789 Capital and co-founder of Rockbridge Network with JD Vance. | Structural bridge only. These roles do not prove control over public decisions. |
| Omeed Malik | Founder/president of 1789 Capital and reported co-founder of the private Executive Branch club. | Corporate and club affiliation is not proof of quid pro quo. |
| Donald Trump Jr. | Partner at 1789 Capital and reported co-founder of the private club. The firm held a disclosed Vulcan investment before OSC's conditional commitment. | No reviewed source establishes that he requested, shaped, or knew in advance about the Vulcan commitment. His spokesperson and 1789 denied involvement. |
| Michael Kratsios | Official biography documents a former Thiel Capital principal role; the White House identifies him as OSTP director. | Career crossover is a network edge, not proof of Palantir-specific influence or misconduct. |
| Jacob Helberg | Financial disclosure documents a senior-adviser role to Palantir's CEO; the Senate confirmed him as a State Department under secretary. | Career crossover is a personnel edge, not proof of procurement influence or misconduct. |
| Peter Navarro | White House trade/manufacturing counselor; ProPublica attributed the request that initiated or accelerated Vulcan's OSC review to him. | Attributed and contested. It does not establish a request from Trump Jr., preferential treatment, skipped diligence, closing, or disbursement. |
| Donald Trump | Issuer of EO 14243. | The order is vendor-neutral and does not name Palantir. |
| Peter Thiel | Founder-network endpoint connecting Palantir and Thiel Capital. | Founder/investment roles do not by themselves establish control over public officials or awards. |

## Vulcan evidence boundary

The Office of Strategic Capital officially announced a **$620 million conditional commitment** to Vulcan Elements. The official release says funds are not disbursed before due diligence, satisfaction of conditions, and financial close.

ProPublica attributed the White House request behind the review to Peter Navarro. That edge is recorded as `attributed_investigative_reporting`, marked contested, and accompanied by the relevant denials. No primary request document, completed closing, or disbursement record was established in this pass.

## Graph rules applied

1. Important graph endpoints use canonical `starintel:*` string IDs.
2. Metadata arrays are not treated as graph edges until an explicit `relation` record exists.
3. Employment, investment, friendship, club affiliation, and policy alignment are not converted into misconduct claims.
4. Conditional financing is kept distinct from closing and disbursement.
5. Reported intervention remains attributed unless primary records resolve it.

## Remaining targets

- White House–OSC–Pentagon communications and the original Vulcan intake/request record;
- Vulcan credit review, conditions precedent, closing, and disbursement records;
- Kratsios and Helberg ethics agreements, recusals, and participation records;
- Executive Branch club ownership, event, guest, and official-contact ledger, without treating attendance as causation.

## Validation

The added database records were checked for valid JSON, unique IDs, v0.9.0 top-level fields, string-valued relation endpoints, and explicit evidence boundaries for contested and conditional claims.
