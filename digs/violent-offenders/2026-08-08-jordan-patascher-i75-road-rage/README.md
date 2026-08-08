# Jordan T. Patascher — I-75 road-rage firearm incident

Dataset: `violent-offenders`  
Schema: StarIntel Document `0.9.0`  
Packet date: 2026-08-08  
Consumer path: `digs/violent-offenders/2026-08-08-jordan-patascher-i75-road-rage`

## Classification

Included in `violent-offenders` based on direct video evidence and law-enforcement-based reporting of a July 29, 2026 road-rage encounter on southbound I-75 near U.S. 301 / Exit 254 in Hillsborough County, Florida.

Current 2026 criminal charges are **pending adjudication**. The packet does not describe those charges as convictions.

## Victim handling

Victim identities are intentionally omitted. No victim `person`, `user`, `address`, `phone`, `email`, or other identifying entity documents are created.

## Incident

- Subject: Jordan T. Patascher
- Incident: road-rage encounter involving an apparent handgun
- Date/time: July 29, 2026, shortly before 6:30 p.m. EDT
- Location: southbound I-75 near U.S. 301 / Exit 254, Hillsborough County, Florida
- Arrest: July 31, 2026 by Pasco County Sheriff's Office in connection with the Hillsborough County investigation
- Reported charges:
  - aggravated assault with a deadly weapon
  - possession of a firearm by a convicted felon
  - driving with a revoked license as a habitual offender
- Injuries: none reported by the sheriff's office announcement

## Geography

The StarIntel v0.9.0 schema supports:

- `dtype: "location"`
- `dtype: "geo"`
- common top-level `geospatial` metadata

This packet uses all three where appropriate.

The public report identifies the incident only as southbound I-75 near the U.S. 301 exit. Coordinates are therefore an **approximate interchange anchor**, not an assertion that the incident occurred at the exact point:

- Exit 254 / I-75 at U.S. 301
- approx. `27.90335, -82.34381`

## Evidence posture

The strongest evidence is the HCSO-released video reproduced/embedded in public reporting. FOX 17 describes the video as showing the SUV driver holding what appears to be a handgun near an open window and pointing it toward the other vehicle.

The historical-record section is deliberately conservative. A secondary booking aggregator contains prior arrests and a 2025 habitual-offender revoked-license sentence notation, but the packet does **not** convert unverified historical arrest entries into convictions. The current convicted-felon status is recorded as law-enforcement-based reporting until the underlying felony docket is independently resolved.

## Documents

- `starintel:dataset-manifest:violent-offenders-patascher-2026-08-08` — `dataset-manifest` — Violent offenders — Jordan Patascher I-75 road-rage packet manifest
- `starintel:source:reddit-floridagawker-patascher-road-rage-2026-08` — `source` — Road rage, convicted felon with a fire arm and suspended license. Hit the trifecta.
- `starintel:source:fox17-patascher-road-rage-2026-08-04` — `source` — Video shows driver pointing gun during I-75 road rage incident, deputies say
- `starintel:source:arrests-org-patascher-2025-02-17` — `source` — Jordan Patascher Mugshot | 02/17/25 Florida Arrest
- `starintel:source:fdot-i75-exit-numbers` — `source` — Interstate Exit Numbers for I-75
- `starintel:source:turnpikes-i75-us301-exit254` — `source` — Interstate 75 At US 301
- `starintel:person:jordan-t-patascher` — `person` — Jordan T. Patascher
- `starintel:location:i75-us301-exit-254-hillsborough` — `location` — I-75 / U.S. 301 interchange (Exit 254), Hillsborough County, Florida
- `starintel:geo:i75-us301-exit-254-hillsborough` — `geo` — Geo node — I-75 / U.S. 301 Exit 254
- `starintel:media:hcso-patascher-i75-dashcam-video` — `media` — HCSO-released dashcam/video evidence of I-75 road-rage incident
- `starintel:event:patascher-i75-road-rage-2026-07-29` — `event` — I-75 road-rage firearm incident involving Jordan Patascher
- `starintel:legal-case:patascher-hillsborough-road-rage-2026` — `legal-case` — Hillsborough County road-rage prosecution/arrest — Jordan Patascher
- `starintel:evidence-record:patascher-video-firearm-display` — `evidence-record` — Video evidence: firearm displayed/pointed from SUV
- `starintel:evidence-record:patascher-threat-reported-by-investigators` — `evidence-record` — Evidence: investigators reported threat and handgun display
- `starintel:evidence-record:patascher-license-plate-switch` — `evidence-record` — Evidence: alleged post-incident license-plate switch
- `starintel:evidence-record:patascher-arrest-and-charges-2026-07-31` — `evidence-record` — Evidence: arrest and current charges
- `starintel:evidence-record:patascher-no-injuries-reported` — `evidence-record` — Evidence: no injuries reported
- `starintel:evidence-record:patascher-2025-habitual-revoked-license-sentence` — `evidence-record` — Historical evidence: 2025 habitual-offender revoked-license sentence
- `starintel:evidence-record:patascher-reported-convicted-felon-status` — `evidence-record` — Evidence: current reporting identifies convicted-felon status
- `starintel:claim:patascher-current-aggravated-assault-charge` — `claim` — Current aggravated-assault charge
- `starintel:claim:patascher-current-felon-firearm-charge` — `claim` — Current felon-in-possession charge
- `starintel:claim:patascher-current-revoked-license-habitual-offender-charge` — `claim` — Current habitual-offender revoked-license charge
- `starintel:claim:patascher-video-depicts-firearm-pointing` — `claim` — Video depicts firearm pointing during road-rage encounter
- `starintel:claim:patascher-reported-convicted-felon-status` — `claim` — Reported convicted-felon status
- `starintel:relation:patascher-participant-in-i75-road-rage-event` — `relation` — participant-in
- `starintel:relation:i75-road-rage-event-occurred-at-exit254` — `relation` — occurred-at
- `starintel:relation:patascher-defendant-in-2026-road-rage-case` — `relation` — defendant-in
- `starintel:relation:dashcam-video-documents-i75-road-rage-event` — `relation` — documents
- `starintel:relation:geo-node-represents-exit254-location` — `relation` — represents-location
- `starintel:research-pass:patascher-violent-offenders-normalization-2026-08-08` — `research-pass` — Jordan Patascher violent-offenders normalization pass

## Files

- `README.md`
- `sources.md`
- `starintel-documents.jsonl`
