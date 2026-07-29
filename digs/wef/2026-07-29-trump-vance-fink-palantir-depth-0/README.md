# WEF–Trump–Vance–Fink–Palantir convergence — depth 0

**Dataset:** `wef`  
**Date:** 2026-07-29  
**Recursion depth:** 0  
**Schema:** StarIntel v0.9.0  
**Records:** 3

## Research question

What directly documented relationships connect the World Economic Forum, Donald Trump, JD Vance, Larry Fink, BlackRock, Palantir and Peter Thiel?

## Core finding

The seed graph is an overlap of three typed networks:

```text
WEF governance and partner network
  -> Larry Fink / BlackRock
  -> Palantir / Alex Karp

Trump political network
  -> JD Vance
  -> presidential business and technology advisers

Thiel–Palantir network
  -> Peter Thiel
  -> Vance employment, political support and venture relationships
```

The evidence supports **network convergence**, not a single command structure.

## Direct edges added

| Edge | Relationship class | Evidence |
|---|---|---|
| Larry Fink → WEF | co-chair / formal governance | Official WEF leadership page |
| Palantir → WEF | 2026 Annual Meeting partner | Official WEF partner roster |
| BlackRock → WEF | 2026 Annual Meeting partner | Official WEF partner roster |
| Larry Fink ↔ Alex Karp | named WEF session speakers | Official WEF event page |
| Donald Trump → WEF | 2026 special address | Official WEF transcript |
| Donald Trump → Larry Fink | presidential advisory appointment | Presidential archive |
| BlackRock → Palantir | reported beneficial holdings | Palantir 2026 SEC proxy |

Existing AutoDig records supply the already-established paths:

```text
Donald Trump -> JD Vance -> Peter Thiel -> Palantir
Larry Fink -> BlackRock
Alex Karp -> Palantir
```

## Bounded conclusions

- **Peter Thiel** remains the strongest person-level route from Vance into Palantir.
- **Larry Fink** is the strongest WEF-to-finance bridge.
- **Palantir** is the strongest organization-level crossover.
- BlackRock's reported Palantir holdings do not establish control.
- Event participation and partner status do not prove coordination or membership.

## Dataset rule

All newly emitted records for this investigation use the existing `wef` dataset. Existing normalized entity IDs from earlier AutoDig packets are reused rather than duplicated.

## Next recursive target

```text
starintel:investigation-target:wef-trump-vance-fink-palantir-depth-1
```

Depth 1 resolves personnel and institutional bridges with at least two paths back to this seed graph:

- Michael Kratsios
- David Sacks
- Jacob Helberg
- Trae Stephens
- Joe Lonsdale
- Rockbridge Network
- Founders Fund
- Anduril
- 8VC
- PCAST
