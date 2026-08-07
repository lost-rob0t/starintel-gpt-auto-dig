# WEF–Columbus citywide-membership reconciliation — depth 10

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 10  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 6

## Reconciliation

- authorization ceiling: **$150,000**
- authorization-compatible invoices: **16**, totaling **$127,846**
- unique paid checks: **15**, totaling **$127,631**
- remaining ceiling after compatible invoices: **$22,154**
- remaining ceiling after unique paid checks: **$22,369**
- direct WEF-related payees: **0**

The $215 difference between invoice and unique-check totals is not counted twice. Two National PELRA invoices were linked by the bounded resolver to the same $215 paid check, so one invoice remains independently unresolved.

## Payees

The identified portfolio consists of municipal, legal, procurement, labor-relations, management, news, and human-resources associations or services. It includes National League of Cities, Ohio Municipal League, U.S. Conference of Mayors, NIGP, Columbus Bar Association, municipal-law associations, ICMA, procurement associations, PELRA, SHRM, and Hannah News Service.

No reconciled payee names the World Economic Forum, Global Shapers, Young Global Leaders, Davos, or the Centre/Center for Urban Transformation.

## Evidence boundary

The public Accounting Distribution dataset omits the main-account code, so the published data cannot directly prove account `63975` on each row. Compatibility is based on all six available authorization dimensions: Finance / Financial Management / General Fund / Contractual Services / Financial management / General Fund Operating.

The large working joins were reduced to `reconciliation-compact.json`; the canonical packet preserves the evidence boundary, payee totals, line-item identifiers, and unresolved residual without retaining duplicate intermediate payloads.

## Depth 11 target

`starintel:investigation-target:wef-depth-11-citywide-membership-main-account-and-residual`

This target seeks main-account-bearing distributions, invoice backup, the remaining $22,369 authorization balance, and resolution of the duplicated $215 PELRA link.

## Validation

- 6 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `801133a87e87c6ce092853c7e0f10fdff15614896c5a92ad79d13f9f5082bbb2`
- deterministic gzip SHA-256: `9c90ed172b1101f1027124ef840c27607a53c7a17230a8e1480d87a0a8aa3b84`
- base64 transport SHA-256: `23b4ecdb39861844b8a17fa9bbcb1fea265ddc9011dabe278a05bf9fb299dbb1`
