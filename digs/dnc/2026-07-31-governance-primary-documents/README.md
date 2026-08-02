# DNC governance primary documents

Official-source seed packet for the current DNC governing rules and the 2024 convention/delegate-selection framework.

## Contents

- 3 official PDF source records
- 3 governing-document nodes
- 3 DNC-to-document relations
- 12 recursive investigation targets
- 21 StarIntel documents total

## Official documents

1. **DNC Charter and Bylaws — October 2025**
   - Complete page/provision extraction
   - Historical version and amendment comparison
   - Enumeration of every charter-created body, office, and public roster
   - Public decisions, waivers, appeals, discipline, and enforcement history
2. **2024 Call for the Democratic National Convention**
   - Page, rule, appendix, formula, deadline, and allocation extraction
   - Reproduction and reconciliation of every delegate allocation
   - Complete convention committee, officer, and delegation-role enumeration
   - Implementation, waiver, vendor, system, and dispute history
3. **2024 Delegate Selection Rules — Final Revised**
   - Page and rule extraction
   - Complete corpus of state, territorial, District of Columbia, and Democrats Abroad plans
   - Waiver, challenge, penalty, remedy, appeal, and disposition history
   - People, committees, staff, counsel, vendors, systems, and outside ties

## Evidence handling

Normative rule text is represented as published requirements, not as proof that every requirement was followed. Compliance, violations, disputes, waivers, findings, and dispositions require separate source-backed records. Private ballots, credentials, private contact data, residential addresses, and non-public membership records are excluded.

```bash
python3 scripts/materialize_dnc_governance_primary_documents.py
python3 scripts/validate-for-merge.py --site
```
