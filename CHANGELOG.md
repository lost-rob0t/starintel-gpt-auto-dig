# Changelog

## Unreleased

### 2026-08-08

- Fixed missing source references in the original violent-offenders legal-case packet in place.
- Added the existing plea, sentencing, and charging reports directly to the legal-case record's `sources` array and bumped the record version.
- Updated the full merge-gate workflow so `db/**` and `digs/**` changes run the complete site validation automatically.
- No correction packet was added.
