# ShotSpotter: surveillance scope and locality recursion

Generated: `2026-07-26T23:45:00-04:00`

This pass answers the hard question directly: **ShotSpotter does more than listen for bangs.** Its core system continuously senses ambient audio, keeps a temporary local audio buffer, can incidentally capture intelligible voices near impulsive events, preserves incident audio, and can estimate the location and movement of a suspected shooter. It is **not by itself a persistent person-identity tracker** like facial recognition or ALPR.

The bigger surveillance risk is the integration chain. ShotSpotter alert data can trigger or feed CAD, RMS, RTCC, CCTV, drones, license-plate readers, access-control systems, crime dashboards, and investigative platforms. A momentary acoustic event can therefore become a broader visual, vehicle, entity, and case-record investigation.

## Output

- **100 StarIntel v0.9.0 documents**
- gzip/base64 multipart transport: `starintel-documents.jsonl.gz.b64.parts`
- locality subset: Columbus/CPD, New York City/NYPD, Chicago/CPD, Durham/DPD, Oakland/OPD
- 19 sources
- 15 organizations
- 6 products
- 2 contracts
- 3 policies
- 19 claims
- 6 analyses
- 19 relations
- 9 recursive targets

## Assessment

**Classification: conditionally harmful / high-governance-risk.**

The evidence does not support calling ShotSpotter universally useless or universally beneficial.

- Durham found more detections, faster response, 73 ShotSpotter-only confirmed shootings, and seven attributable arrests, but no demonstrated improvement in shooting-investigation productivity.
- NYC found only 8–20% of alerts produced confirmed shootings in sampled months; June 2023 produced 426.9 officer-hours on unconfirmed or unfounded alerts.
- Chicago found gun-related criminal evidence in 9.1% of dispatched alerts and documented alert-linked investigatory stops; its inspector general also found that frequent alerts changed some officers' perceptions and interactions.
- Oakland supplies a governance comparator through a public surveillance impact report, use policy, and privacy oversight.
- Columbus renewed ShotSpotter for two years and $1.323 million, but this pass did not locate a public independent Columbus effectiveness audit or end-to-end integration map.

## Tracking boundary

### Documented core capability

- continuous acoustic sensing and algorithmic analysis
- temporary ambient-audio buffering
- incidental human-voice capture near qualifying events
- permanent incident snippets
- vendor-mediated missed-shot lookback within the buffer window
- precise event geolocation
- estimated shooter position, movement, direction, and—in Columbus's ordinance—speed

### Not established

- persistent identity tracking by the ShotSpotter microphone system itself
- facial recognition by core ShotSpotter
- automatic person or vehicle dossiers from a ShotSpotter-only purchase
- that Columbus enabled every integration advertised by SoundThinking
- exact automated integration between Columbus ShotSpotter and Flock

## Recursive locality subset

The locality subset was chosen for distinct evidence value:

1. **Columbus** — anchor locality; current contract, explicit movement language, Flock coexistence, unresolved architecture.
2. **New York City** — large deployment and detailed municipal audit.
3. **Chicago** — large historical dataset, stop analysis, and documented behavioral effects.
4. **Durham** — independent evaluation containing meaningful counterevidence and a non-renewal decision.
5. **Oakland** — public surveillance-governance comparator.

## Hard pass/fail controls for a locality

A locality should not keep or expand ShotSpotter without:

- incident-level alert and outcome exports
- independent confirmation-rate and victim-aid analysis
- officer-hours and opportunity-cost reporting
- explicit ban on stops or searches based only on an acoustic alert
- complete audio retention, missed-shot request, download, and subpoena logs
- public integration inventory for CAD/RMS/RTCC/CCTV/drones/ALPR
- public third-party and federal-sharing rules
- demographic and geographic deployment analysis
- sunset, audit, and termination clauses
- publication of policy violations and corrective actions

## Evidence boundary

The 2019 Policing Project privacy audit is valuable but not fully independent: it disclosed unrestricted SoundThinking funding, payment for audit time and travel, and the vendor CEO's advisory-board role. Vendor privacy controls are recorded as vendor assertions unless a locality-specific audit verifies them. Precise sensor locations are excluded.
