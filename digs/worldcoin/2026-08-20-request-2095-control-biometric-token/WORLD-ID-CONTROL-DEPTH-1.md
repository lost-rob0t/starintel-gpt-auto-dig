# WHO HOLDS THE KEYS? — World ID control depth 1

Request: #2095 (`worldcoin-eyeball-empire-v1`)

## The short version

World ID is not a contract system where nobody can change anything.

The still-production World ID 3.0 codebase explicitly documents two privileged roles. The **owner** is intended to be a multisig. The **identity operator** is intended to use an OpenZeppelin Relay wallet.

The owner can replace the identity operator, turn the state bridge on or off, replace verifier tables, change the Semaphore verifier, change the state bridge, transfer ownership, and upgrade the Identity Manager implementation. The identity operator can register and delete identity commitments.

World ID 3.0 is being sunset, not switched off overnight. Its own repository says it remains actively used in production while migration to World ID 4.0 proceeds.

World ID 4.0 does not make privileged administration disappear. The current `WorldIDBase` contract inherits OpenZeppelin `Ownable2StepUpgradeable` and `UUPSUpgradeable`. Upgrade authorization is restricted to the proxy owner. The proxy owner can also change the fee recipient, fee amount, and fee token.

That answers one part of **CAN SOMEBODY FLIP THE SWITCH?**: the public code contains explicit owner-gated control points.

It does **not** yet answer who holds the live production owner wallet today.

## What the evidence proves

| system | documented authority | privileged actions | controller identity status |
|---|---|---|---|
| World ID 3.0 Identity Manager | owner multisig | upgrade implementation; enable/disable state bridge; replace identity operator; replace verifier tables; change root expiry/Semaphore verifier/state bridge; transfer ownership | wallet/signers not resolved in this pass |
| World ID 3.0 Identity Manager | identity operator / OpenZeppelin Relay-associated wallet | register and delete identity commitments | current wallet/legal operator not resolved in this pass |
| World ID 4.0 `WorldIDBase` | proxy owner | authorize UUPS upgrades; change fee recipient, fee amount, and fee token | production owner/multisig/legal controller unresolved |

## What this does not prove

An `onlyOwner` modifier does not tell us whether World Foundation, Tools for Humanity, Sam Altman, another entity, or a mixed multisig controls the live production owner address.

The development/anvil wallet shown in the 3.0 README is not a production key and is not treated as one.

Repository architecture is not a substitute for reading the live proxy and owner state.

## Next target

`starintel:investigation-target:worldcoin-world-id-4-production-admin-authority-depth-2`

Recover the canonical production World ID 4.0 proxy and implementation addresses, resolve current owners and privileged roles on-chain, then attribute multisigs/signers/legal controllers only where first-party or independently corroborated evidence supports it. Preserve signer thresholds, timelocks, emergency powers, and upgrade/key-rotation history separately.

## Primary sources

- World ID 3.0 Contracts, “Privileged Actions and Trust”: https://github.com/worldcoin/world-id-contracts/blob/main/README.md
- World ID 4.0 `WorldIDBase.sol`: https://github.com/worldcoin/world-id-protocol/blob/main/contracts/src/core/abstract/WorldIDBase.sol
