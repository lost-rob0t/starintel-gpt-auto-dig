# Request #1900 — Cornell Flock data-control / retention evidence pass

## Scope

Bounded continuation of issue #1900. This pass reuses the existing Cornell Flock target identities and does **not** create another campus network, camera inventory, or sharing edge.

## New evidence isolated in this pass

The March 4, 2026 *Cornell Daily Sun* report contains a materially useful attributed institutional statement that was not carried forward as its own evidence state in the prior #1900 packet:

- the report says Cornell University Police Department (CUPD) had a contract to operate seven Flock cameras on campus;
- a Cornell University spokesperson told the paper the cameras had operated since October 2024;
- the same spokesperson stated that **CUPD owns the data in the Flock database and that it is accessible for up to 30 days before automatic deletion**.

Source: https://www.cornellsun.com/article/2026/03/cornell-students-express-concern-over-flock-safety-ai-camera-usage-on-campus

This is preserved as an **attributed institutional statement reported by an independent publication**, not as a recovered contract, native Flock configuration export, or deletion certificate.

## Reconciliation with current Policy 8.1

Cornell's current University Policy 8.1, updated August 18, 2026, supplies a different evidence layer: a 14-day university recorded-security-video baseline with preservation exceptions, plus centralized visibility requirements unless a camera is exempted.

Primary policy: https://policy.cornell.edu/policy-library/physical-security-systems

The two values are therefore kept separate:

- `reported_flock_data_access_window`: 30 days — attributed to a University spokesperson in March 2026;
- `university_security_video_policy_baseline`: 14 days — current Policy 8.1 as of August 18, 2026;
- `actual_flock_configured_retention`: unresolved;
- `flock_policy_8_1_integration_or_exemption`: unresolved;
- `deletion_execution`: unresolved.

## What this advances

The prior issue body listed ownership/control as unresolved. This pass narrows that correctly:

- **reported data controller/owner:** CUPD, per the University spokesperson statement;
- **hardware ownership / lease / maintenance responsibility:** unresolved;
- **contractual data-rights language:** unresolved because the native contract is still missing;
- **actual user/admin roster and platform permissions:** unresolved;
- **actual 30-day configuration and historical change log:** unresolved;
- **directed CUPD ↔ Ithaca Police sharing:** unresolved.

No private-person data is collected. No inference is made from policy authority to Flock credentials or from reported data ownership to actual sharing/query activity.
