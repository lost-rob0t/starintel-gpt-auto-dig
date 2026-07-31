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
- Canonical JSONL SHA-256: `69056149df883843198097ac1bbb62f2c2c5457256c7db17d0fd60a369b611ed`
- Gzip SHA-256: `c662918677038977cefdaa0aeb9a1c0e90ffc9048e3bf7a6e800e68811dcb569`
