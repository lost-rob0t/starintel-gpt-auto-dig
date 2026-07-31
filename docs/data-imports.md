# External data imports

## Topic datasets

The generated site builds two dataset layers:

- **topic datasets** merge records from every matching research target and source dataset;
- **source datasets** preserve the original `dataset` values and target-specific browsers.

`manifests/topic-datasets.json` defines umbrella topics such as `wef`, `ohio`, `offshore-leaks`, and `occrp-aleph`. A research target that matches no umbrella rule gets its own topic dataset automatically. Records may belong to more than one topic when the evidence is genuinely cross-topic.

The obsolete `daily` source dataset is excluded from the generated source catalog. Its records remain available through their research targets and are assigned to topical datasets by the same rules.

Generated outputs:

```text
_site/topic-datasets.json
_site/dataset-<topic>/index.html
_site/dataset-<topic>/downloads/starintel-documents.jsonl
_site/dataset-<topic>/downloads/topic-manifest.json
```

The topical JSONL preserves the original canonical documents and their source `dataset` values. It is a merged view, not a duplicate normalized corpus.

## Encrypted iPhone backups

`scripts/extract_iphone_backup.py` decrypts a local encrypted backup, saves a decrypted `Manifest.db`, preserves domain and relative-path folders, and emits a hashed extraction report.

```bash
python3 -m pip install iphone_backup_decrypt
export IPHONE_BACKUP_PASSWORD='...'
python3 scripts/extract_iphone_backup.py \
  --directory /path/to/MobileSync/Backup/DEVICE-ID \
  --output imports/iphone-backup \
  --password-env IPHONE_BACKUP_PASSWORD
```

See [`docs/iphone-backup-extraction.md`](iphone-backup-extraction.md) for filtering, incremental extraction, and the required StarIntel `source` + `email-message` + `person` import transaction.

## ICIJ Offshore Leaks

The importer reads the official ICIJ CSV archive and emits validated StarIntel JSONL. By default it selects Paradise Papers and Offshore Leaks records.

```bash
python3 scripts/import_icij_offshore_leaks.py \
  --download \
  --output imports/icij-paradise-offshore.jsonl

python3 scripts/starintel.py import imports/icij-paradise-offshore.jsonl
```

Use `--all` for every investigation in the archive, or repeat `--investigation` to select specific source datasets. Use `--limit` for a bounded test import.

The importer preserves ICIJ node IDs, source investigation names, original CSV rows in provenance metadata, official source attribution, and ICIJ's identity-matching caveat.

## OCCRP Aleph

The Aleph importer queries entities visible to the current account and converts FollowTheMoney entities into validated StarIntel JSONL.

```bash
ALEPH_API_KEY='...' python3 scripts/import_aleph_public.py \
  --query 'World Economic Forum' \
  --query 'Ohio' \
  --limit 1000 \
  --output imports/occrp-aleph.jsonl

python3 scripts/starintel.py import imports/occrp-aleph.jsonl
```

Use `--collection <id>` to restrict a query to one accessible Aleph collection. The importer does not bypass Aleph access controls. When the public endpoint exposes no matching entities, an API key or a different public collection/query is required.

## InfluenceWatch

`scripts/import_influencewatch.py` converts InfluenceWatch person, organization, nonprofit, labor-union, government-agency, political-party, and influence-network profiles into validated StarIntel v0.9 JSONL under the `influence-watch-db` dataset. It emits typed profile records, a source record, publisher-attributed internal-link relations, and a dataset manifest.

InfluenceWatch's Terms of Use effective May 1, 2026 prohibit scraping, crawling, automated harvesting, and systematic downloading without express written consent. Network collection is therefore disabled unless authorization is explicitly acknowledged with `--authorized` or `INFLUENCEWATCH_AUTHORIZED=1`. The importer also enforces `robots.txt`, throttles requests, retries transient failures, and caps response sizes.

After obtaining written authorization, run a bounded crawl first:

```bash
INFLUENCEWATCH_AUTHORIZED=1 python3 scripts/import_influencewatch.py \
  --crawl \
  --limit 100 \
  --delay 2 \
  --output imports/influence-watch-db.jsonl

python3 scripts/starintel.py import imports/influence-watch-db.jsonl
```

Use `--url` or `--url-file` for authorized targeted imports. Existing HTML acquired through an authorized channel can be normalized without network access:

```bash
python3 scripts/import_influencewatch.py \
  --input imports/influencewatch/example-profile.html \
  --output imports/influence-watch-db.jsonl
```

Profile claims, ideological characterizations, and internal links remain explicitly attributed to InfluenceWatch until independently corroborated. The importer does not treat an internal link as proof of a substantive relationship.
