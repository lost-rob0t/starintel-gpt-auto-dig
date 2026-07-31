# Federal executive branch cabinet and advisers — pass 1

Current-role graph for the U.S. executive branch, cut off **July 31, 2026**.

## Added graph

- **21** current cabinet and cabinet-level officials.
- **7** verified senior White House or Executive Office advisers/officials.
- All represented departments, cabinet-level agencies, and EOP components.
- `heads`, `acting_head_of`, `member_of`, `advises`, `serves_in`, succession, prior-role, and selected prior-affiliation relations.
- Two recursive verification targets.

## Live ODNI transition

The Office of the Director of National Intelligence still listed **William J. Pulte** as Acting DNI at the cutoff. The Senate confirmed **Walter “Jay” Clayton III** on July 28, 2026. The graph therefore does **not** overwrite Pulte prematurely:

- Pulte remains `acting_head_of` ODNI.
- Clayton is represented as `confirmed_to_succeed` Pulte.
- A high-priority target tracks Clayton’s swearing-in, Pulte’s formal end date, and the ODNI roster update.

## Acting officials

- Todd Blanche — Acting Attorney General.
- William J. Pulte — Acting Director of National Intelligence.
- Keith E. Sonderling — Acting Secretary of Labor.

## Evidence discipline

Official White House, ODNI, Senate, and agency sources are primary. Associated Press is used only for the very recent Clayton confirmation that had not yet propagated through the official ODNI roster. Prior affiliations are limited to relationships stated in official biographies; they are not treated as evidence of improper influence.

## Packet

- Core records: **188**
- Relations: **105**
- Persons: **31**
- Organizations: **48**
- Recursive targets: **2**
- Canonical JSONL SHA-256: `2ceb1425fed2641246b70e3fae9480c875ce02c37c2bae45214104c25ff3bd85`
- Gzip SHA-256: `36611a873618814a20205df888774d0d9b85ed06f26ce621b26e4729c4b0eea2`


## Schema normalization

Legacy packet-only fields and original values requiring type coercion were preserved under `extensions.legacy_data`; target questions and preferred sources were mapped into declared StarIntel v0.9 fields.
