# Changelog

## Unreleased

### 2026-08-09

- Added a source-backed Di-Quan Schafar Hunt packet to the `violent-offenders` dataset for the July 30, 2026 filmed Charlotte assault.
- Located and recorded the viral video repost plus local-news video coverage while preserving uncertainty about original-upload provenance.
- Normalized the reported repeat-offender history as **at least nine prior arrests/releases**, not nine convictions.
- Separately recorded the court-record-based December 2025 case that ended in a March 18, 2026 plea, 89 days served, and a time-served sentence.
- Kept the current 2026 allegation marked pending adjudication and omitted victim identifiers.

### 2026-08-08

- Fixed missing source references in the original violent-offenders legal-case packet in place.
- Added the existing plea, sentencing, and charging reports directly to the legal-case record's `sources` array and bumped the record version.
- Updated the full merge-gate workflow so `db/**` and `digs/**` changes run the complete site validation automatically.
- No correction packet was added.