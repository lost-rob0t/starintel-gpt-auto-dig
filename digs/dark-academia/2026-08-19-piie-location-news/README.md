# PIIE Washington location and current-news pass

Global dataset-first selection chose `piie-public-roster` from the 54-entry current Auto-Dig dataset/topic universe using reproducible seed `2036112764371671481` after recent-run and direct-conflict exclusions.

PIIE first-party contact and annual-report pages publish **1750 Massachusetts Avenue, NW, Washington, DC 20036-1903**. They do not explicitly call the address headquarters, so this packet models it as the Institute's primary public office. PIIE's organization-managed LinkedIn profile separately labels Washington, DC as headquarters and the same street address as its primary location; that label is preserved as an attributed `reported_headquarters_at` relation rather than silently promoted to first-party fact. No coordinates are asserted.

After the location slice, current PIIE news was searched from the July 31 roster baseline through August 19, 2026. PIIE's August 3 press release announced that trade expert **Inu Manak joined as a senior fellow**. The packet adds her source-bounded person record, personnel-announcement event, and current senior-fellow relation.

The recursive target is explicit headquarters designation plus current official staff/board roster recovery, because the July `piie-public-roster` manifest still reports zero parseable people.

Canonical source dataset remains `piie`; no new dataset is created.
