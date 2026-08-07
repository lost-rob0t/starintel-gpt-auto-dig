# USAspending award-transaction collector

`scripts/scrape_usaspending_award_transactions.py` retrieves the modification and obligation history for the three public FBI Threat Screening Center award records currently under investigation.

## Default awards

| Award | Generated USAspending ID | Investigative purpose |
|---|---|---|
| BAE TSC Analysis Services | `CONT_AWD_15F06725F0001209_1549_GS00F240CA_4732` | Reconstruct initial award, later obligations, deobligations and disposition |
| BAE TSC bridge | `CONT_AWD_15F06725F0001838_1549_GS00F240CA_4732` | Reconstruct bridge timing and overlap |
| IntelliWare TSC Intelligence Analysis Services | `CONT_AWD_15F06726F0000362_1549_GS10F0473Y_4732` | Reconstruct the later active award and funding sequence |

## Run

```bash
python3 scripts/scrape_usaspending_award_transactions.py \
  --output imports/fbi-procurement/transactions.jsonl
```

Add or replace targets explicitly:

```bash
python3 scripts/scrape_usaspending_award_transactions.py \
  --generated-award-id CONT_AWD_15F06726F0000362_1549_GS10F0473Y_4732 \
  --output /tmp/intelliware-tsc-transactions.jsonl
```

## Output fields

Each JSONL record contains:

- `generated_award_id`;
- stable transaction identity when supplied by USAspending;
- official award URL;
- retrieval timestamp;
- SHA-256 of the canonical transaction payload;
- unmodified transaction payload.

The payload may expose action dates, modification numbers, action types, descriptions, and federal obligation values. The collector preserves these records; it does not infer whether a negative obligation represents cancellation, corrective action, termination, administrative adjustment, or another mechanism.

## Investigative use

The transaction sequence should be compared against:

- award and bridge dates;
- GAO and Court of Federal Claims dockets;
- FBI corrective-action records;
- termination or cancellation notices;
- unsuccessful-offeror notices;
- the later IntelliWare award.

A deobligation pattern can support a replacement hypothesis, but the legal or acquisition mechanism remains `not_established` until an authoritative record states it.

## Validation

```bash
python3 -m unittest tests.test_scrape_usaspending_award_transactions -v
python3 -m compileall -q scripts/scrape_usaspending_award_transactions.py
```
