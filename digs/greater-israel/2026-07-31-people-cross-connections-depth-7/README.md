# Greater Israel people and cross-connections — depth 7

**Run:** `2026-07-31`  
**Existing dataset:** `greater-israel-aipac-enablement-2026-07-26`  
**Root target:** `starintel:target:greater-israel-us-israeli-enablement`  
**Schema:** StarIntel `0.9.0`  
**Recursion depth:** `7` of `8`  
**Documents:** `38`

## Set-intersection method

This pass used a small deterministic set-ranking script rather than repeatedly expanding every person in prose.

For a person with `n` independently sourced cluster memberships, the screening score is:

```text
pairwise intersections = n × (n - 1) / 2
```

The score only prioritizes research. It is not a measure of guilt, control, influence, or wrongdoing.

Files:

- `bridge-memberships.json` — sourced cluster memberships used for screening;
- `rank-bridge-sets.py` — deterministic ranking script;
- `starintel-documents.jsonl.gz.b64` — deterministic gzip/base64 transport containing 38 StarIntel records;
- `quasar-import-manifest.json` — record counts and SHA-256 verification metadata.

Run:

```bash
python3 rank-bridge-sets.py bridge-memberships.json --pretty
base64 -d starintel-documents.jsonl.gz.b64 | gzip -dc > starintel-documents.jsonl
```

Decoded JSONL SHA-256: `73358afba6a5b2e2dd4b91f7005e4d4c0b417c085fab1dd599ca2f9717c5cff9`  
Deterministic gzip SHA-256: `adb62d281deb518bb37f4a4aacde2ef1e8fc38fe6dd0117e70ebda1b44025e03`

## Highest-ranked bridge

### Jules Trump: four sets, six pairwise intersections

Jules Trump appears in four independently sourced clusters:

1. **Foundation family:** the Eddie and Jules Trump family created the Israeli education foundation.
2. **Industrial ownership:** Jules and Eddie Trump controlled the ownership chain running through the Trump Group and Trans-Resource Inc. to Haifa Chemicals.
3. **Direct Netanyahu contact:** Netanyahu's office acknowledged that Netanyahu and Jules Trump were acquainted.
4. **State regulatory intervention:** Netanyahu convened ministers and officials to examine delaying the court-ordered closure of Haifa's ammonia tank.

The Prime Minister's Office denied that the acquaintance influenced the decision. It said Netanyahu had not spoken with Jules Trump for more than a year and had never discussed the tank with him.

Jules Trump later wrote Netanyahu directly regarding the Haifa Chemicals shutdown, losses, ammonia supply and government-promised alternatives.

Supported path:

```text
Eddie and Jules Trump family
  -> Israeli Trump Foundation
  -> Jules Trump
  -> Trump Group
  -> Trans-Resource Inc.
  -> Haifa Chemicals
  -> ammonia-tank litigation and regulation
  -> Netanyahu-led government review
```

This is now the strongest direct person-to-government cross-connection in the foundation branch.

## Other named bridges

### Eli Hurvitz

The foundation's executive director bridges:

```text
Trump Foundation management
  + Yad Hanadiv / Rothschild-family philanthropy
  + prior staff work for the chair of the
    Knesset Foreign Affairs and Defense Committee
```

The identity of the committee chair and Hurvitz's dates of service remain unresolved.

### Michal Cohen

Rashi's current general director previously served as director general of the Education Ministry.

```text
Rashi Foundation
  <-> Michal Cohen
  <-> Israel Ministry of Education
```

Rashi and the Ministry are both core 5p2 institutions. This is a career and institutional bridge; it does not prove that Cohen founded or controlled 5p2.

### Bella Abrahams

Intel's Bella Abrahams stated that she was part of the team that led formation of 5p2. She also described Intel engineers and engineers from 25 other companies volunteering in schools.

```text
Intel Israel
  -> Bella Abrahams
  -> 5p2 formation
  -> industry engineer mobilization
  -> schools
```

The official foundation record separately says the coalition planned to recruit volunteers from high tech, universities and the IDF.

### Michal Beller

Michal Beller bridges foundation governance or advice, RAMA and 5p2's measurement work:

```text
Trump Foundation governance/advice
  -> Michal Beller
  -> founding CEO of RAMA
  -> 5p2 collaboration with RAMA
  -> national data collection and annual progress reporting
```

This is an institutional overlap. It does not establish that Beller personally directed 5p2's measurement work.

### Gideon Sa'ar and Benjamin Netanyahu

The foundation states that Prime Minister Netanyahu and then-Education Minister Gideon Sa'ar presented the inaugural Trump Master Teacher Award.

This creates a direct public-event edge:

```text
Trump Foundation
  -> branded national teaching award
  -> Benjamin Netanyahu
  + Gideon Sa'ar
```

Award participation is not evidence of financial control or policy capture.

## What the expanded graph now shows

The foundation branch now intersects:

- family philanthropy;
- fertilizer and chemical ownership;
- prime-ministerial acquaintance and correspondence;
- industrial regulation and litigation;
- Rothschild-family philanthropy;
- Knesset defense-oversight staffing;
- Education Ministry administration;
- national education measurement;
- Intel and wider high-tech volunteer mobilization;
- government participation in foundation-branded events;
- IDF and defense-R&D participation in the wider 5p2 coalition.

The evidence supports a distributed institutional network. It does not support collapsing every edge into one coordinated command structure.

## Depth-8 target

Queued:

`starintel:investigation-target:greater-israel-people-cross-connections-primary-records-depth-8`

Priority records:

1. PMO minutes, legal submissions and ministerial correspondence from the 2017 ammonia-tank dispute.
2. Corporate registry records for Trump Group, Trans-Resource Inc. and Haifa Chemicals.
3. The full 5p2 steering committee and the twelve named interview subjects behind Sheatufim's case study.
4. Eli Hurvitz's Knesset employment dates and the identity of the committee chair he assisted.
5. Foundation board minutes and source records for government participation.

## Evidence boundaries

- Netanyahu's acquaintance with Jules Trump is acknowledged, but claimed influence is disputed.
- Regulatory intervention is not proof of favoritism.
- Career movement between government and philanthropy is not proof of capture.
- Coalition participation does not prove command.
- Award presentation does not prove a financial relationship.
- A set-intersection score is a research queue, not a culpability score.

## Main sources

- Trump Foundation family background:  
  <https://www.trump.org.il/en/about/background>
- Trump Foundation team and Eli Hurvitz biography:  
  <https://www.trump.org.il/en/team>
- Trump Foundation board:  
  <https://www.trump.org.il/en/about/board-of-directors>
- 5p2 national coalition and government collaboration:  
  <https://www.trump.org.il/en/grant/5p2>
- Trump Master Teacher Award:  
  <https://www.trump.org.il/en/grant/trump-master-teacher-award-2014>
- Rashi Foundation leadership:  
  <https://rashi.org.il/en/team/>
- Intel account of Bella Abrahams and engineer mobilization:  
  <https://community.intel.com/t5/Blogs/Intel/CSR/The-Exponential-Power-of-Collaboration-for-STEM-Success/post/1333752>
- Netanyahu, Jules Trump and the ammonia-tank delay:  
  <https://www.timesofisrael.com/netanyahu-seeks-to-delay-closure-of-controversial-ammonia-tank/>
- Haifa Chemicals ownership chain:  
  <https://en.globes.co.il/en/article-Tene-in-talks-on-stake-in-Haifa-Chemicals-1001355965>
- Jules Trump's letter to Netanyahu:  
  <https://en.globes.co.il/en/article-haifa-chemicals-closes-two-plants-lays-off-800-1001199614>
