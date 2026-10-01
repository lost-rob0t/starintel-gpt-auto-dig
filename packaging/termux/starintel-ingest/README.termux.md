# StarIntel ingest for Termux

This package is the native Android/Termux build of the StarIntel threaded bulk-ingest client.
It accepts canonical StarIntel JSONL on standard input and sends bounded `/documents/bulk`
requests to the configured ingest host.

## Install

Pick the `.deb` matching `dpkg --print-architecture`, then install it with Termux `apt`:

```sh
apt install ./starintel-ingest_0.9.1_*.deb
```

The package installs both command names below; they point at the same native binary:

- `starintel-ingest`
- `starintel-ingest-core`

## Authenticate

The API key is read only from the environment. It is never accepted as a command-line
argument, so it does not leak through the process list.

```sh
export STAR_SERVER_API_KEY='star_sk_v1_...'
```

The default service is `https://ingest.starintel.actor`. Override it with either
`STAR_INGEST_URL` or `--server-url`.

## Ingest JSONL

Every non-empty input line must be a JSON object with non-empty `_id` and `dtype` fields.

```sh
starintel-ingest < starintel-documents.jsonl
```

Tune concurrency and request size when needed:

```sh
starintel-ingest \
  --workers 4 \
  --batch-size 500 \
  < starintel-documents.jsonl
```

`--workers 0` is automatic and never chooses more than the current per-principal server
concurrency of four workers. The client does not retry ambiguous POST failures, preventing
silent duplicate ingestion when the server may already have accepted a batch.

## CI bundle

GitHub Actions publishes one aggregate `starintel-ingest-termux-all` artifact containing the
Termux `.deb` for each supported architecture plus `SHA256SUMS` and `MANIFEST.txt`.
