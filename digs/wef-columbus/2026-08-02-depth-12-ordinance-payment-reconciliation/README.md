# Smart Columbus ordinance-to-payment reconciliation — depth 12

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 12  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 9

## Result

- confirmed ordinance-attributed payments: **$5,051,132.50**
- exact aggregate candidate for `0165-2021`: **$235,750.00**
- unattributed program expenses: **$37,327.04**
- reconciled direct paid-check total: **$5,324,209.54**

## Critical corrections

- Check `672135` is split into an $85,000 Ride & Drive component and a separate $36,000 Emissions Mapping Pilot component.
- The `0165-2021` pair is an exact aggregate candidate, not a confirmed attribution.
- The explicit `1581-2021` chain contains a $10,050 amount difference that requires authority records; impropriety is not established.

## Depth 13 target

`starintel:investigation-target:wef-depth-13-smart-columbus-authority-gaps-and-vendor-master`

## Validation

- 9 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `4246da3419077f6a386752b2010d025e977e486942e66f8bafdb2c5ef51f12b3`
- deterministic gzip SHA-256: `b27121f4676ba8c1e2f124b4ef627d6a71c3b18513671f4587930293dda32153`
- base64 transport SHA-256: `536941e6627e851dfc865d5518ded7c0c07cbaf2f1db90e766a4fe869e18a01c`
