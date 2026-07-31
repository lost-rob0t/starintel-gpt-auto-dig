# Encrypted iPhone backup extraction

Use `scripts/extract_iphone_backup.py` to decrypt a local encrypted iPhone backup before corpus parsing and StarIntel import.

## Install the optional extractor dependency

```bash
python3 -m pip install iphone_backup_decrypt
```

`fastpbkdf2` is optional and can reduce the initial key derivation time:

```bash
python3 -m pip install fastpbkdf2
```

## Complete extraction

The safest password path is an environment variable or the interactive prompt. Avoid `--password` when shell history or process listings are a concern.

```bash
export IPHONE_BACKUP_PASSWORD='...'
python3 scripts/extract_iphone_backup.py \
  --directory /path/to/MobileSync/Backup/DEVICE-ID \
  --output ./imports/hunter-biden-iphone \
  --password-env IPHONE_BACKUP_PASSWORD
```

The extractor writes:

```text
imports/hunter-biden-iphone/
├── Manifest.db
├── call_history.sqlite
├── extraction-report.json
└── files/
    └── <domain>/<original relative path>
```

Domain subdirectories and original folder paths are preserved so identically named files from different applications do not overwrite each other.

## Filtered extraction

Both filters use SQLite `LIKE` syntax from the backup manifest.

```bash
python3 scripts/extract_iphone_backup.py \
  --directory /path/to/backup \
  --output ./imports/mail-only \
  --domain-like 'AppDomain-com.apple.mobilemail%' \
  --relative-path-like '%'
```

Decrypt only the manifest:

```bash
python3 scripts/extract_iphone_backup.py \
  --directory /path/to/backup \
  --output ./imports/manifest-only \
  --manifest-only
```

Resume a large extraction without rewriting files that are not newer in the backup:

```bash
python3 scripts/extract_iphone_backup.py \
  --directory /path/to/backup \
  --output ./imports/hunter-biden-iphone \
  --incremental
```

## Failure handling

The extractor does not silently discard decryption or filesystem errors. A missing optional call-history database is recorded as `not-found`; other failures terminate with a non-zero exit code. The JSON report records the filters, manifest hash, extracted-file count, timestamps, and call-history status.

## StarIntel import rule

Decryption is only source preparation. Each imported email must still produce, in one research transaction:

1. a canonical `source` document;
2. a canonical `email-message` document;
3. `person` documents for the sender and recipients;
4. source-scoped `person` documents for explicit body mentions that are not safely resolved;
5. stable links among the source, message, and people.

Do not treat an extracted file, screenshot, or generic message record as a completed email import.
