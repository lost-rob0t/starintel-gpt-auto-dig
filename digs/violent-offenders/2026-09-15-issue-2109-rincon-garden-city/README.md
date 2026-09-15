# Alberto Rincon / Garden City robbery seed — bounded pass

Issue: #2109

This pass resolves the ambiguous seed to the publicly reported **Alberto Rincon / Garden City, Kansas** incident chain without promoting arrest allegations into convictions.

## Findings

Three contemporaneous public reports independently reproduce Garden City Police Department-attributed facts:

- On **May 4, 2024**, officers responded to an armed robbery at Joyeria America in Garden City. Reporting says a man held an employee at gunpoint and stole property.
- On **July 1, 2024**, officers responded to an armed robbery at Tacos El Tapatio. Reporting says a man held employees/customers at gunpoint and left with money.
- On **July 4, 2024**, police attempted to stop Alberto Rincon, then 49, in Garden City. Reporting says he fled by vehicle, the pursuit ended east of the city, and he was taken into custody after running from the vehicle.
- The reports attribute to Garden City Police the statement that investigators identified Rincon as the suspect in both robbery investigations.
- The reports list requested/arrest charges after the July 4 arrest, including two aggravated-robbery counts and additional pursuit/firearm/drug-related allegations. These are **reported arrest/requested-charge states only** in this packet.

## Evidence boundary

This pass did **not** locate an authoritative Finney County charging instrument, criminal case number, docket, judgment, plea/trial disposition, or sentence. It therefore does not create a final-disposition claim or convert any requested charge into a conviction.

The person and incident records retain `draft` / allegation semantics pending the native court/police join. A separate investigation target carries the unresolved chain:

`Garden City PD native release/report → Finney County complaint/information → case number → docket → disposition/sentence`

No private address, private phone, personal email, family information, credentials, private account, or victim identity is collected. Public business names are retained only as incident identifiers.

## Sources

- KWCH, 2024-07-05: https://www.kwch.com/2024/07/05/wichita-man-arrested-armed-robberies-garden-city/
- The Wichita Eagle, 2024-07-06: https://www.kansas.com/news/local/crime/article289814769.html
- Hutch Post, 2024-07-06: https://hutchpost.com/posts/73a6e48e-f051-4d69-a53e-96b172c4fa0f

## Canonical write path

The adjacent `starintel-documents.jsonl` is the source packet. Normalized `db/` surfaces must be produced only by the repository importer:

```bash
python3 scripts/starintel.py import \
  digs/violent-offenders/2026-09-15-issue-2109-rincon-garden-city/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```

The branch materialization workflow successfully ran the canonical importer and repository validation before committing the resulting `db/` surfaces. Do not hand-copy packet records into `db/`.