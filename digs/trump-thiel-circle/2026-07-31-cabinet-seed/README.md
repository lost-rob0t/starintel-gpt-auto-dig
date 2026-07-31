# trump-thiel-circle — current Trump cabinet seed

**Run:** `trump-thiel-circle-seed-2026-07-31`
**Dataset:** `trump-thiel-circle`
**Roster cutoff:** `2026-07-31`
**Schema:** StarIntel `0.9.0`

This pass seeds every current White House cabinet member, then expands:

`person → issue/claim → connected organization → officers/members → Trump/Vance/Thiel path`

Evidence status is explicit: `official-finding`, `official-corrective-action`, `official-inquiry`, `watchdog-complaint`, `civil-allegation`, `historical-allegation`, `investigated-no-action`, `conflict-exposure`, `documented-connection`, or `open-research`.

A connection edge is not automatically a corruption finding. Claims retain denials, rebuttals, dismissals, and no-action dispositions.

## Coverage

| dtype | count |
|---|---:|
| source | 32 |
| person | 34 |
| org | 78 |
| relation | 140 |
| claim | 26 |
| research-pass | 1 |
| **total** | **311** |

The recursive queue contains all **21** cabinet members.

## Cabinet-wide findings matrix

| Person | Office | Lead | Status | Key organizations / path |
|---|---|---|---|---|
| Scott Bessent | Treasury | Missed ethics-agreement divestiture deadlines; Treasury said 96% complete and remainder illiquid. | official finding | Key Square → Treasury → Trump |
| Todd Blanche | Acting AG | Former Trump criminal-defense lawyer; Senate inquiry alleges disregard of recusal advice. | official inquiry | Trump legal team → Blanche → DOJ |
| Doug Burgum | Interior | Oil-and-gas royalties and attendance at Harold Hamm-organized Mar-a-Lago oil meeting. | documented conflict | Continental Resources/Hess → Hamm → Trump |
| Doug Collins | Veterans Affairs | No substantiated personal corruption finding in seed; procurement and privatization recursion queued. | open research | VA → Trump |
| Sean Duffy | Transportation | Sponsored-road-trip and spouse-book promotion complaints; BGR revolving-door exposure. | complaint/conflict | Boeing/Toyota/United/BGR → DOT |
| William J. Pulte | Acting DNI / FHFA | Reported firing of Fannie ethics staff examining an ally. | reported misconduct | Fannie/Freddie/FHFA → Trump targets |
| Jamieson Greer | USTR | King & Spalding and transition revolving-door exposure. | conflict exposure | King & Spalding → Trump–Vance Transition → USTR |
| Pete Hegseth | War/Defense | Pentagon IG reportedly found Signal use created operational-security risk. | official finding | DOD/Signal → Trump |
| Robert F. Kennedy Jr. | HHS | Retained contingency/referral-fee interest in Merck litigation while controlling health regulators. | documented conflict | Wisner Baum/Merck → HHS → Trump |
| Kelly Loeffler | SBA | COVID-era stock-trade investigation; DOJ closed inquiry and Senate Ethics found no violation evidence. | investigated-no-action | ICE/Bakkt/Jeffrey Sprecher → SBA |
| Howard Lutnick | Commerce | Cantor/Tether reserve and crypto-policy conflict. | documented conflict | **Lutnick → Cantor → Tether → $775M Rumble ← Thiel/Vance backing** |
| Linda McMahon | Education | Civil suit alleges McMahons/WWE enabled ring-boy abuse; claims denied/contested. | civil allegation | WWE/TKO/AFPI → Trump |
| Markwayne Mullin | Homeland Security | House Ethics required $40,000 repayment after outside-income/company-role review. | official corrective action | Mullin Plumbing → House Ethics → Trump |
| John Ratcliffe | CIA | 2019 DNI nomination withdrawn amid qualification and résumé controversy. | historical allegation | ODNI/CIA → Trump |
| Brooke Rollins | Agriculture | AFPI/TPPF donor-policy and revolving-door pipeline. | conflict exposure | TPPF → AFPI → USDA/Trump |
| Marco Rubio | State | Florida GOP charge-card controversy; reimbursements and no-wrongdoing disposition preserved. | investigated-no-action | Florida GOP → Rubio → Trump |
| Keith Sonderling | Labor | Employer-side Gunster practice into Labor enforcement. | conflict exposure | Gunster clients → DOL → Trump |
| Scott Turner | HUD | JPI/consulting/Opportunity Zone beneficiary network requires contract tracing. | open conflict research | JPI/CEOC/AFPI → HUD/Trump |
| Russ Vought | OMB | Project 2025/Heritage/CRA power network. | documented network | **Vought → Project 2025/Heritage → Kevin Roberts ← Vance foreword; Vought → Trump OMB** |
| Chris Wright | Energy | Former Oklo board role prompted conflict allegation; DOE says compliant and no Oklo stock. | allegation with rebuttal | Liberty/Oklo/EMX → DOE/Trump |
| Lee Zeldin | EPA | Qatari-led Heritage Advisors payment and post-nomination PAC contribution tied to former plastics executive. | documented payment/reported conflict | Heritage Advisors/PAC → EPA/Trump |

## Strongest clear paths

### Howard Lutnick → Tether → Rumble ← Peter Thiel / J.D. Vance

1. Lutnick led **Cantor Fitzgerald** and co-chaired the **Trump–Vance Transition Team**.
2. Cantor managed a large portion of **Tether** reserves.
3. Tether invested **$775 million** in **Rumble**.
4. Rumble was backed by **Peter Thiel** and **J.D. Vance-related capital**.
5. Rumble went public through Cantor-affiliated **CF Acquisition Corp. VI**.

This is the strongest cabinet-to-Thiel/Vance corporate-finance path in the seed. It is a documented network; it does not alone prove a corrupt agreement.

### Russ Vought → Project 2025 / Heritage → Kevin Roberts ← J.D. Vance

Vought founded **Center for Renewing America**, led **Heritage Action**, contributed to **Project 2025**, and returned to Trump’s OMB. **J.D. Vance** wrote the foreword to Heritage president **Kevin Roberts’** book.

### Doug Burgum → Harold Hamm / Continental Resources → Trump

Burgum disclosed oil-and-gas royalty interests, attended the Hamm-organized Mar-a-Lago oil-executive meeting, and then received Interior and National Energy Council authority. A quid pro quo remains a hypothesis, not an established fact.

### Todd Blanche → Trump defense counsel → DOJ leadership

The White House states Blanche represented Trump in three criminal cases. A Senate inquiry alleges he later participated in Trump-related matters despite recusal advice.

## Priority recursion

1. **Pulte:** FHFA/Fannie personnel files, board minutes, IG complaints, referral chains, and communications involving Trump targets.
2. **Lutnick:** Cantor ownership transfers, Tether reserve mandates, Rumble SPAC records, Commerce/crypto contacts, and transition appointments.
3. **Blanche:** DOJ ethics advice, recusal memoranda, waivers, matter list, settlement records, and communications.
4. **Vought:** Project 2025 authors, CRA/Heritage donors, appointees, OMB actions, and Vance-linked personnel.
5. **Collins / Greer / Rollins / Sonderling / Turner:** OGE filings, client lists, lobbying, recusals, contracts, grants, and nonprofit donors.
6. **Wright:** Oklo, Liberty, and EMX interests against DOE decisions, grants, fuel policy, and recusals.
7. **Zeldin:** Heritage Advisors principals/work product, PAC separation, plastics donors, EPA actions, and communications.

## Materialize the dataset

The canonical payload is deterministically gzip-compressed and base64-split across:

- `seed-parts/seed-part-01.b64`
- `seed-parts/seed-part-02.b64`
- `seed-parts/seed-part-03.b64`
- `seed-parts/seed-part-04.b64`
- `seed-parts/seed-part-05.b64`

Run:

```sh
python build-starintel.py
```

The builder validates dataset/schema identity, rejects duplicate record IDs, and writes:

- `starintel-documents.jsonl`
- `research-queue.json`

The payload includes full source URLs, evidence classifications, claims, organizations, people, relations, clear connection paths, and the 21-target recursive queue.
