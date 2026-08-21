# IISS Arundel House headquarters and current-news pass

This hourly Auto-Dig pass used the live 54-surface dataset/topic universe and a reproducible dataset-first seed of `7829785773918349329`. The previous three successful hourly datasets, `bruegel-public-roster`, `rockefeller-foundation-public-roster`, and `usaid-doge-mortality-accountability`, were hard exclusions; Brussels, New York, and Washington, D.C. were also avoided at target selection when alternatives existed.

The dataset-stage draw selected the `dark-academia` composite. Deterministic target draws rejected recently completed HQ work, active overlapping PRs, and repeated Washington/New York geography until selecting the existing `iiss-public-roster` target `starintel:org:international-institute-for-strategic-studies`.

## Headquarters result

Current first-party IISS evidence explicitly identifies Arundel House as the Institute's London headquarters. The official contact page gives the address as **Arundel House, 6 Temple Place, London WC2R 2PG** and separately publishes IISS offices in Washington, Singapore, Bahrain, and Berlin. The packet therefore adds an exact `headquarters` location and a `headquartered_at` relation without collapsing those other offices into the headquarters predicate.

No coordinates are added. No registered-office or legal-seat claim is inferred from the headquarters evidence. A recursive target queues authoritative legal-seat and dated headquarters-continuity resolution.

## Current-news result

Only after the location semantics were fixed, current IISS press, careers, publication, appointment, partnership, and location surfaces were searched through 2026-08-19. The current material reviewed consisted of vacancies, publications, and event promotion; the IISS press index's newest listed partnership/organizational release was dated 2026-06-29. No material organizational, governance, relationship, or location change justified a filler event.

## Records

The packet contains seven v0.9.0 records: three sources, one location, one relation, one queued investigation target, and one completed research pass. The canonical source dataset remains `iiss`; no per-run dataset is created.
