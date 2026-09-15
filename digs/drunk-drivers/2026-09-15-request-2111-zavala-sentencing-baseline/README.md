# Request #2111 — Eugenio Les Zavala sentencing baseline

Worker 7/8 bounded continuation of #2111 under the canonical `drunk-drivers` dataset.

This slice promotes the already source-grounded fifth-case prosecution and Texas sentencing-law baseline into canonical StarIntel records without pretending the missing native court records are resolved.

## Records

- 1 `source`
- 1 `analysis`
- 1 `research-pass`

## Evidence boundary

The Montgomery County District Attorney's official press-release index confirms a `State of Texas vs. Eugenio Les Zavala` release dated July 23, 2026. A local republication explicitly authored by the DA's office reports the July 20–21, 2026 221st District Court trial, DWI (Third or More) conviction, 50-year jury punishment, warrant-obtained 0.150 blood result, self-representation with standby counsel, and the prosecution claim that prior felony convictions established habitual-offender status.

Texas Penal Code §49.09(b)(2) independently establishes the felony-DWI rule for two qualifying prior intoxication-operation convictions. Texas Penal Code §12.42(d) independently establishes the life-or-25-to-99-year habitual-felony range when two qualifying final felonies satisfy the sequential-finality requirement. Texas Code of Criminal Procedure art. 37.07 independently establishes that jury punishment depends on the applicable statutory election procedure.

This packet does **not** infer which two felony predicates were actually used, the cause number, the contents of the indictment, a valid self-representation waiver, the written punishment election, an actual parole-eligibility date, or a native appellate filing. Those remain unresolved until primary records land.

## Canonical materialization

The packet must be materialized with the repository writer/import path:

```sh
python3 scripts/starintel.py import \
  digs/drunk-drivers/2026-09-15-request-2111-zavala-sentencing-baseline/starintel-documents.jsonl
```

Issue #2111 remains open after this bounded pass because its completion criteria require the full five-DWI chronology, exact felony predicates, native fifth-case record, verified parole mechanics, appellate posture, comparator set, and claim-by-claim reconciliation.