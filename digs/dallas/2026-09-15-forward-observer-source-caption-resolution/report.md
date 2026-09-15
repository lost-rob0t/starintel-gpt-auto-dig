# Forward Observer Dallas source/caption resolution — issue #2578

## Scope

This bounded pass resolves two ambiguities in the existing Dallas/Forward Observer packet without silently rewriting the earlier source record:

1. the local-media reporting behind the Dallas protest permit/DPD coordination claim; and
2. the phrase rendered as “young active labor leaders.”

The existing `starintel:source:forward-observer-briefing-v78Syf14qs4` remains a claim pointer. New records add independently retrievable provenance and explicit correction edges.

## Findings

### Local-media source chain

The local Dallas report is Austin Wood’s *Dallas Observer* article, **“Dallas cancels permit for anti-Trump protest 1 week before GOP convention begins,”** published September 2, 2026. The report says the Office of Special Events canceled the planned Sept. 10 march permit and records a Dallas Police Department statement that DPD preferred organizers work directly with police rather than continue through the special-event permit process.

The already-landed Christian Post source independently reports the same permit-process rationale and names Allison Hudson, assistant director of DPD’s Office of Media Relations and Community Affairs. The new packet therefore links the Dallas Observer source to the Forward Observer briefing only for the permit-process claim; it does **not** treat that corroboration as validation of every assertion in the video.

### YALL caption/name resolution

The ambiguous phrase resolves to **Young Active Labor Leaders Dallas-Fort Worth (YALL DFW)**, not a generic class of “young active labor leaders.”

Public evidence used:

- DFW YALL’s Action Network group page identifies the local group as “Young Active Labor Leader Dallas -Ft. Worth,” says it was established in 2014 as part of the Dallas AFL-CIO’s local effort, and describes its labor-organizing mission.
- Texas AFL-CIO’s official constituency-group page establishes the **Young Active Labor Leaders / YALL** name and AFL-CIO young-worker-program context.
- Dallas Express reporting from September 1, 2026 says protest promotional material displayed the **Young Active Labor Leaders Dallas-Fort Worth** logo.

The packet records the Dallas Express evidence as a **promotional-material association only**. It does not infer formal coalition membership, attendance, endorsement of other organizations, or any personal membership.

## Canonical records prepared

`starintel-documents.jsonl` contains:

- 4 source records;
- 1 organization record (`starintel:org:yall-dfw`);
- 3 provenance-preserving relation records:
  - Dallas Observer corroborates the permit-process portion of the existing Forward Observer source;
  - YALL DFW appears on promotional material for the existing Dallas RNC march event;
  - YALL DFW resolves the ambiguous caption/reference in the existing Forward Observer source.

No private addresses, personal phones, family information, credentials, private accounts, or unrelated personal-life data were collected.

## Import requirement

Per `AGENTS.md` and `skills/create-starintel-documents/SKILL.md`, normalized `db/` records must be written by the transactional batch importer, not by direct GitHub file edits:

```bash
python3 scripts/starintel.py import \
  digs/dallas/2026-09-15-forward-observer-source-caption-resolution/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```

The packet has now been materialized through `scripts/starintel.py import`; the importer-generated normalized `db/` surfaces are committed on this branch. Merge still requires fresh successful exact-head repository workflows, including `Run complete canonical merge gate`.

## Public provenance

- https://www.dallasobserver.com/news/dallas-cancels-permit-for-anti-trump-protest-1-week-before-gop-convention-begins-40710308/
- https://actionnetwork.org/groups/yall-dfw
- https://texasaflcio.org/constituency-groups/texas-young-active-labor-leaders
- https://dallasexpress.com/state/group-that-hosted-james-talarico-event-joins-coalition-with-communist-and-socialist-organizations/
- existing source pointer: https://www.youtube.com/watch?v=v78Syf14qs4
