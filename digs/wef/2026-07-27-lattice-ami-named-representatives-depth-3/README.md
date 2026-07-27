# Lattice–AMI–WEF — named representatives and policy outputs, depth 3

**Dataset:** `wef`  
**Date:** 2026-07-27  
**Recursion depth:** 3  
**Schema:** StarIntel v0.9.0  
**Records:** 29

## Core finding

The Coherent branch now has direct person-level WEF evidence at two points:

- **Vincent D. Mattera Jr.** — then-CEO of II-VI — publicly sponsored the company's 2021 partnership with the World Economic Forum's Advanced Manufacturing & Production Platform.
- **Grace Lee** — Coherent Chief People Officer — is listed by WEF as a current member of the Frontline Talent Excellence Community.

WEF describes that community as a senior-executive network for quarterly peer exchanges and collaborative initiatives shaping manufacturing-workforce practices. Its public outputs include workforce playbooks and the 2025 *Empowering Frontlines* white paper.

Coherent is also listed in WEF's Chief Operating, Supply Chain & Procurement Officers Community, but the public record does not identify Coherent's delegate.

## Semiconductor policy path

Semiconductor Industry Association President and CEO **John Neuffer** publicly advocated for the Building Chips in America Act. WEF later published an explanatory article describing the enacted law, using SIA data and industry rationale while also noting environmental criticism.

This establishes a policy-amplification path:

```text
Lattice CEO Ford Tamer
  -> SIA board

SIA President John Neuffer
  -> advocated for Building Chips in America Act

WEF
  -> published policy summary citing SIA rationale and data
```

It does **not** establish joint authorship, joint lobbying, acquisition control or a WEF role in negotiating the Lattice–AMI deal.

## Negative and bounded findings

The reviewed public record does not identify:

- a current Lattice employee serving as Lattice's named WEF representative;
- Coherent's delegate to the WEF operations and supply-chain officers community;
- a specific recommendation, vote or publication section authored by Grace Lee;
- a WEF consumer-hardware ownership, BIOS subscription or firmware kill-switch policy tied to Lattice or AMI.

The concrete WEF outputs found at this layer concern workforce transformation, human-machine collaboration and manufacturing/supply-chain strategy.

## Record inventory

| Dtype | Count |
|---|---:|
| `source` | 9 |
| `org` | 2 |
| `person` | 3 |
| `policy` | 1 |
| `event` | 1 |
| `relation` | 10 |
| `analysis` | 1 |
| `investigation-target` | 1 |
| `research-pass` | 1 |

## Next recursive target

```text
starintel:investigation-target:lattice-ami-firmware-standards-governance
```

Depth 4 moves from institutional links to the technically decisive layer:

- UEFI Forum
- DMTF and Redfish
- Trusted Computing Group
- Open Compute Project
- NIST SP 800-193
- firmware signing-key custody
- authenticated updates and anti-rollback
- recovery authority
- Aptio, MegaRAC, Tektagon and Lattice Sentry
- consumer repairability, third-party firmware and end-of-support licensing

The stop condition remains bounded: capability or standards participation must not be converted into malicious intent without product, contract or policy evidence.
