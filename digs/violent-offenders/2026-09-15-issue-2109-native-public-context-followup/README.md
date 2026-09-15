# Issue #2109 — Garden City native/public context follow-up

Worker 5/8 bounded follow-up to the already-merged #2651 packet.

## Added evidence

- **Primary city record:** the City of Garden City September 3, 2024 commission packet contains the Garden City Police Department July 2024 Master Activity Report. It records one robbery offense in July and, in the investigations table, two robbery cases assigned and one cleared during July. The report is aggregate-only: it does **not** name Alberto Rincon, Joyeria America, or Tacos El Tapatio and does not expose an incident, complaint, or court case number.
- **Earlier incident chronology:** KWCH's May 6, 2024 report, explicitly attributing the incident facts to Garden City police, places the May 4 Joyeria America robbery at **308 E. Fulton Street** and predates the later public identification of Rincon.
- **Preserved contradiction:** later reporting / issue prose has rendered that address as **308 W. Fulton**. This packet does not silently choose one. The E/W direction remains unresolved until a stronger native record resolves it.

## Legal-state guardrail

The new primary city report is useful aggregate context, not a deterministic identity join. It does not establish that any July robbery row corresponds one-to-one with the Tacos El Tapatio event or with Rincon, and it does not establish filed charges, conviction, disposition, or sentence. The existing `starintel:investigation-target:rincon-finney-county-native-case-disposition` therefore remains open.

## Remaining native-record gaps

- Garden City Police incident/arrest report IDs for May 4, July 1, and July 4, 2024.
- Finney County complaint/information and exact criminal case number.
- Filed, amended, or dismissed counts.
- Plea/trial disposition, judgment, and sentence.
- Primary resolution of the Joyeria America 308 E. vs 308 W. Fulton discrepancy.

## Transactional materialization

`starintel-documents.jsonl` is the authoritative packet for this bounded pass. The branch uses the repository's canonical `scripts/starintel.py import` path to materialize normalized `db/` records; generated DB surfaces are not hand-written.
