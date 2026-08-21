# USAID former headquarters and State OIG transfer pass

This hourly Auto-Dig pass used the repository's global dataset-first selector. The complete candidate universe contains 54 datasets/topics. The previous-three successful hourly datasets (`chatham-house-public-roster`, `boao-forum-public-roster`, and `graphika`) were excluded, together with their dominant London/United Kingdom, China/Beijing-Hainan, and New York geographies when alternatives existed.

The reproducible 64-bit run seed is `1075698361894339645`. The first draw over the recency-filtered pool landed on `occrp-aleph`, but its sole recorded investigation target is blocked by lack of visible collections and its manifest contains no imported organization IDs. It was therefore recorded as non-actionable for the mandatory HQ phase rather than silently treated as usable. Re-indexing the remaining actionable pool with the same seed selected `usaid-doge-mortality-accountability`. A target-stage seed of `17222205892484988458` selected `o:usaid` from the sorted organization pool `o:doge`, `o:state`, `o:usaid`, `o:whitehouse`.

## HQ / location result

A current USAID Office of Inspector General page identifies **USAID OIG Headquarters** at the Ronald Reagan Building, **1300 Pennsylvania Avenue NW, Washington, DC 20523**. The corpus already identifies USAID as `o:usaid`. Because USAID's independent operating structure was dismantled and selected functions were transferred to the Department of State in July 2025, this pass does not pretend the address is a current USAID-wide headquarters. It adds a typed `location` plus a `formerly_headquartered_at` relation and explicitly queues the exact agency-wide occupancy end date for further verification. No coordinates are invented.

## Current-news / oversight result

After the location slice was bounded, current official oversight and news surfaces were searched. State Department OIG report `AUD-FA-26-17`, issued July 23, 2026, is a material update to this dataset: OIG found that 17 State bureaus and offices were administering 1,504 transferred USAID programs and associated awards with $51.5 billion in obligated value, while documenting staffing, training, IT/data-access, and guidance challenges. Prior May 2025 realignment recommendations were not fully implemented as of July 2026.

The packet adds seven typed v0.9.0 records: two `source` records, one `location`, one `relation`, one `event`, one `investigation-target`, and one `research-pass`. The canonical dataset remains `usaid-doge-mortality-accountability`; no new dataset or parallel schema is introduced.
