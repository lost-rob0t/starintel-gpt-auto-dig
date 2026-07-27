# WEF SmartStart USA — launch coalition and state leads, depth 3

**Dataset:** `wef`  
**Date:** 2026-07-27  
**Recursion depth:** 3  
**Schema:** StarIntel v0.9.0  
**Records:** 23

## Core finding

The January 21, 2026 public launch of SmartStart USA connected the World Economic Forum's manufacturing centre to state government, organized labor, industrial automation, workforce staffing and semiconductor manufacturing.

Official and institutional sources identify the launch participants as:

- Kiva Allgood — World Economic Forum
- Gretchen Whitmer — Governor of Michigan
- Andy Beshear — Governor of Kentucky
- Randi Weingarten — American Federation of Teachers
- Blake Moret — Rockwell Automation
- Becky Frankiewicz — ManpowerGroup
- Sanjay Mehrotra — Micron Technology

WEF separately states that more than 60 leaders from government, education and labor collaborated on industry-ready curricula and pathways to credentials, training, internships and hiring.

## Analytic boundary

Participation in the Davos launch does **not** establish that Michigan or Kentucky hosts the August 2026 pilot. It does establish that both governors were directly present in the public launch coalition, making their states evidence-based priority leads for procurement, school, budget and workforce-record searches.

## Record inventory

| Dtype | Count |
|---|---:|
| `source` | 4 |
| `org` | 4 |
| `person` | 7 |
| `event` | 1 |
| `relation` | 5 |
| `analysis` | 1 |
| `investigation-target` | 1 |
| `research-pass` | 1 |

## Next recursive target

```text
starintel:investigation-target:wef-smartstart-michigan-kentucky-pilot-verification
```

The next pass searches Michigan and Kentucky education, workforce, procurement, grant, legislative, school-board and employer records for SmartStart implementation evidence. It must preserve a negative finding if neither state is confirmed.
