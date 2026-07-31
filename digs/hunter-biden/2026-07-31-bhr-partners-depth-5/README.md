# Hunter Biden — BHR Partners expanded target enumeration and lead attack

**Dataset:** `hunter-biden`  
**Run:** `2026-07-31-bhr-partners-depth-5`  
**Schema:** StarIntel v0.9.0  
**Status:** source-ranked research-lead packet

## What this pass does

This pass decomposes the remaining BHR graph into **38 leaf investigation targets**. Each target contains concrete source types, search strings, official registries, expected evidence, and the entities it can resolve.

The attack surfaces are:

1. corporate state and post-2023 restructuring;
2. Skaneateles, Ulysses, loans, sale, and cash-flow chronology;
3. directors, shareholder-bloc governance, vetoes, and conflicts;
4. fund/GP/SPV separation and portfolio transaction mapping;
5. authentication, provenance, contradiction analysis, and archival preservation.

## New graph leads

The packet records, with explicit evidence grading:

- official Shenzhen CSRC confirmation that 晟荣星远 participated in the Shenzhen M&A Fund Alliance in January 2025;
- a third-party registry lead reporting a Shenzhen legal identity, RMB 31.7647 million registered capital, and a reworked cap table;
- official SEC evidence that Xin Wang remained described as a BHR venture partner in 2026;
- an official listed-company disclosure identifying Xue Ming as a BHR management-company director;
- source-qualified leads for Li Xiangsheng, Zhaoxin, Shanghai Fengshi, Zhang Liang, Fan Renda, and Zheng Shi;
- source-qualified leads for a D.C. Skaneateles filing copy and a March 2017 Ulysses equity-transfer document.

## Evidence boundary

The registry mirror is not authoritative. Its cap table and officer data are encoded only as `reported_*` relations with official-registry confirmation targets.

The 2017 Ulysses transfer report and D.C. filing copy are leads until authenticated against original custodians.

Congressional questions, characterizations, and requests are not converted into adjudicated findings.

## Counts

- Sources: 7
- Organizations: 3
- People: 6
- Relations: 13
- Investigation targets: 38
- Total records: 67

## Files

1. `sources.jsonl`
2. `entities.jsonl`
3. `relations-1.jsonl`
4. `relations-2.jsonl`
5. `investigation-targets-1.jsonl`
6. `investigation-targets-2.jsonl`
7. `investigation-targets-3.jsonl`
8. `investigation-targets-4.jsonl`
9. `investigation-targets-5.jsonl`
10. `investigation-targets-6.jsonl`
11. `investigation-targets-7.jsonl`
12. `investigation-targets-8.jsonl`
13. `sources.md`
14. `target-matrix.md`
15. `manifest.json`
