# Flock Safety: Columbus 287(g) sharing-control recursion

Generated: `2026-07-31T01:26:00-04:00`

This is the next recursive pass over the Columbus Flock graph. It executes the prior packet's queued **sharing-roster** target and narrows the failure to a temporal access-control problem.

## Resolved

- The four agencies removed after press inquiries were Geauga County Sheriff's Office, Blount County Sheriff's Office, Cheatham County Sheriff's Office, and Spartanburg County Sheriff's Office.
- CPD asked Flock for a 287(g) exclusion control on April 8, 2026.
- CPD disabled national sharing and removed then-known one-to-one 287(g) partners on June 3.
- Spartanburg was missed during that cleanup.
- Geauga, Blount, and Cheatham entered new task-force-model agreements after the cleanup.
- CPD removed all four on July 17.
- Flock said it does not track which agencies enter 287(g) agreements; CPD described monitoring and revocation as an ongoing manual process.

## Core finding

The failure was not just an inaccurate list. It was a **missing continuous reconciliation loop**.

A point-in-time cleanup cannot enforce a policy whose input—agency 287(g) status—changes independently. Flock's customer-control model gives CPD the configuration switch, but it does not supply or maintain the external policy attribute needed to keep that switch correct.

## Counts

- analysis: 2
- event: 5
- investigation-target: 7
- org: 8
- person: 3
- policy: 3
- relation: 10
- research-pass: 1
- total: **39**

## Evidence boundaries

- A 287(g) agreement does not prove every Flock query by that agency concerned immigration enforcement.
- This packet does not claim the four agencies queried Columbus data during the prohibited interval.
- Blount and Cheatham agreement timing remains `late June 2026`; the reviewed source did not expose exact dates.
- Flock's data-control statements are vendor claims.
- The complete CPD one-to-one roster and native configuration export remain unavailable.

## Next recursion

1. Recover the full one-to-one roster with edge timestamps and approvers.
2. Obtain partner-level query logs for the four removed agencies.
3. Identify the eight Tennessee police departments still directly sharing with Columbus.
4. Recover the April 8 Flock support request and implementation response.
5. Build a versioned 287(g) feed and test a fail-closed reconciliation actor.
