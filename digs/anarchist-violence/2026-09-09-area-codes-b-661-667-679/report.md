# Area-code-hunt shard B — 661 / 667 / 679

Bounded organization-enumeration pass for `anarchist-violence`.

## Coverage

NANPA current geographic reporting is the admission authority. Deterministic shard B owns admitted U.S. geographic NPAs where `NPA mod 3 == 1`. This pass processed the next unresolved admitted batch after durable coverage through 646: **661, 667, 679**. No completed NPA was repeated without new evidence.

- **661 — Bakersfield / Antelope Valley, California:** reused the existing canonical **Bakersfield ABCF** identity and existing investigation target after re-verifying the current first-party ABCF contact directory. Added only the missing NPA/locality relation plus fresh source/provenance.
- **667 — Baltimore / central-eastern Maryland overlay:** added **Baltimore Food Not Bombs** and **Baltimore Mutual Aid**. September 2026 Collective Garden event material provides current/recent operational evidence for Baltimore FNB, but its historical `/BmoreFNB` Facebook endpoint remains current-status-unverified. Baltimore Mutual Aid's current public site identifies its operator only by the public pseudonym **Spud**; that pseudonym is preserved without attempting deanonymization.
- **679 — Detroit / inner Wayne County Michigan overlay:** added **Eastside Mutual Aid**, **Detroit Peer Respite**, and **Michigan Mutual Aid Coalition**. 679 is treated as overlay geography only; no claim is made that any organization itself uses a 679 phone number.

## Evidence boundaries

Bakersfield ABCF is the sole retained identity in this batch with explicit anarchist organizational identity. Baltimore Food Not Bombs is retained as Food Not Bombs/anarchist-associated under the existing corpus classification rule without imputing beliefs to participants. Detroit Peer Respite explicitly self-describes as abolitionist crisis care and mutual aid, but is **not** relabeled anarchist. Eastside Mutual Aid and MIMAC retain their first-party direct-action / dual-power / mutual-aid descriptions without ideological upgrading.

Public-person cross-enumeration retained three directly stated organization-role relationships and zero inferred relationships:

- **Spud** — public pseudonym directly used by the person operating Baltimore Mutual Aid; legal identity deliberately unresolved.
- **Jewan Price** — publicly identified as an Eastside Mutual Aid co-founder; current role unresolved.
- **Lance Hicks** — publicly identified as a Detroit Peer Respite founding organizer; current role unresolved. First-name-only mentions on the current first-party site were not treated as independent identity proof.

No same-name/handle-only person merge was performed.

## Materialized StarIntel records

`starintel-documents.jsonl` contains **33 typed v0.9 records**:

- 10 `source`
- 5 new `org`
- 5 new `investigation-target`
- 3 `person`
- 9 `relation` (6 NPA/locality + 3 explicit person↔org)
- 1 `research-pass`

The existing Bakersfield ABCF `org` and investigation target are reused rather than duplicated.

## Stats

- codes attempted: **3**
- hit codes: **3**
- org identities found/reused: **6** — 5 new, 1 reused
- current/recent: **6**
- historical-only: **0**
- explicit current self-described anarchist orgs: **1**
- broader anarchist-associated identities: **2**
- people found: **3**
- explicit person↔org relations: **3**
- inferred person↔org relations: **0**
- person identity collisions: **0**
- conservative distinct exact public social/contact endpoints: **11**
- public communication surfaces: **~20**
- source records: **10**
- distinct source domains: **10**
- unresolved structural/person lead classes: **8**

## Unresolved leads

1. Resolve Baltimore Food Not Bombs' current first-party website/social ownership before promoting `/BmoreFNB` to a current canonical endpoint.
2. Determine whether Baltimore FNB has a current direct organizational relationship to Collective Garden beyond produce redistribution.
3. Map Baltimore Mutual Aid's contributor structure without attempting to deanonymize Spud.
4. Follow Eastside Mutual Aid's current first-party partner/project graph.
5. Resolve Jewan Price's current role status; the co-founder evidence is direct but historical.
6. Resolve additional Detroit Peer Respite founding organizers only where full public identities are independently attributable.
7. Resolve Lance Hicks' current role status without collapsing first-name-only references.
8. Follow MIMAC's current coalition/partner graph and organization-owned X/email endpoints.

No normalized generated `db/` record was hand-edited. The packet follows current repository `AGENTS.md` and v0.9 schema; exact-head repository CI is the executable merge validator.
