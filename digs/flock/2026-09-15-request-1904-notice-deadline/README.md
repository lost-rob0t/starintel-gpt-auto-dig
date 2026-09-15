# Request #1904 — Tompkins County Flock notice-deadline pass

Worker 8/8 bounded additive pass for `alpr-ny-tompkins-county-network`.

## What this adds

This pass keeps four lifecycle predicates separate:

1. **April 14, 2026:** Tompkins County says the Legislature voted 12–1 to terminate its Flock Group, Inc. contract before renewal.
2. **April 28, 2026:** a secondary summary of the official special meeting reports County Attorney Maury Josephson said written notice was required on or before this date to prevent an additional two-year renewal. This remains source-qualified until the native adopted resolution or certified minutes are recovered.
3. **May 28, 2026:** the County's own highlights identify this as the auto-renewal boundary.
4. **Execution/offboarding:** this pass still does **not** establish that notice was actually sent/received, the exact effective contract end, account/credential shutdown, sharing removal, hardware disposition, data deletion, or billing closeout.

A contemporaneous report by Enfield Councilperson Robert Lynch separately describes the adopted resolution as directing the County Administrator and County Attorney to provide timely written termination notice before auto-renewal. That corroborates the existence of a notice requirement but is not substituted for the missing native resolution.

## Sources

- Tompkins County official April 7/14 Legislature highlights
- Tompkins County official April 14 special-meeting recording
- Citizen Portal secondary meeting summary for the reported April 28 notice deadline
- Robert Lynch / Enfield Councilperson contemporaneous secondary report

## Canonicalization

`starintel-documents.jsonl` is the authored packet. Normalized `db/` records must be produced only through the repository's required transactional importer:

```bash
python3 scripts/starintel.py import \
  digs/flock/2026-09-15-request-1904-notice-deadline/starintel-documents.jsonl
```

The native resolution/minutes, executed termination notice and delivery receipt, vendor acknowledgment, final invoice, platform users/admins, credential revocations, `SharedNetworks`, audit exports, device state, and retention/deletion evidence remain open targets.
