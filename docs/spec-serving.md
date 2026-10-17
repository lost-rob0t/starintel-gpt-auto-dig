# Serving the StarIntel spec over HTTP

Status: implemented (branch `spec/http-deployment`)
Authority: the spec artifacts remain `starintel_doc/spec.py` + the generated
JSON Schema + manifest, resolved through `scripts/schema-release.py`. This
document defines how every downstream language consumes them over HTTP.

## Why

Consumers previously had to clone the canonical repository and read local
files. Deployment now serves immutable, versioned, digest-pinned bundles so
that:

- JSON-Schema languages (Python, Nim, JS, CL validators) fetch
  `/schema/<version>`;
- Star-Lang consumers (Common Lisp runtime, portable manifests) fetch
  `/star/<version>` and pin by the same SHA-256 digest the import system
  already requires;
- every client can resolve the current release from `/releases` and pin with
  `/lock/<version>` without knowing repository internals.

The JSON Schema's `$id` already declares the canonical serving domain:
`https://spec.starintel.actor/schema/starintel-doc-<version>.schema.json`.
The server below serves exactly that path shape.

## Service

`scripts/serve-spec.py` is a stdlib-only HTTP registry over a pinned checkout
of this repository:

```bash
python3 scripts/serve-spec.py \
  --root /srv/starintel-gpt-auto-dig \
  --base https://spec.starintel.actor \
  --bind 127.0.0.1 --port 8787
```

Routes:

| Route | Content |
|---|---|
| `GET /releases` | release index with served commit |
| `GET /schema/<version>` | generated JSON Schema for a release |
| `GET /schema/starintel-doc-<version>.schema.json` | canonical `$id` shape |
| `GET /manifest/<version>` | release manifest |
| `GET /star/<version>` | Star-Lang spec-library export |
| `GET /sha256/<version>` | SHA256SUMS of the release bundle |
| `GET /lock/<version>` | consumer lock JSON (digests + commit + URLs) |

Versioned artifacts carry `Cache-Control: public, max-age=31536000, immutable`.

## Star-Lang export

`scripts/star-lang-export.py` regenerates `spec/star/starintel-core-<v>.star`
from `starintel_doc/spec.py` deterministically and records its SHA-256 in
`spec/star/SHA256SUMS`. The library identity is `org.starintel/core@1` with
`:version "<release>"`; one document per dtype extends the shared
`starintel-document` base; enum scalars are generated for enum-typed wire
fields.

The `.star` library is the *semantic* authority (types, fields, requireds)
for Star-Lang consumers. The JSON Schema stays the *wire* authority for the
envelope JSON (snake_case `data` payloads); the export maps snake_case wire
fields to Star-Lang's lower camelCase and expresses nullability through
`:optional`. Regenerate after any vocabulary change with:

```bash
python3 scripts/star-lang-export.py
```

## Consumer workflows

### Star-Lang (Common Lisp)

```lisp
(import "org.starintel/core@1"
  :version "0.10.1"
  :digest "sha256:<digest from /lock/0.10.1>"
  :url "https://spec.starintel.actor/star/0.10.1")
```

Offline or hermetic builds vendor the identical bytes and use `:path` with
the same digest — the digest is computed over the file octets, so a vendored
copy of a committed artifact verifies unchanged.

```bash
starlang load program.star --allow-network \
  --cache .cache/star-lang/specs
```

### Python

```python
import json, urllib.request
lock = json.load(urllib.request.urlopen(
    "https://spec.starintel.actor/lock/0.10.1"))
schema = json.load(urllib.request.urlopen(lock["http"]["schema"]))
# validate with jsonschema against schema; verify lock["schema_sha256"]
```

### Any language over JSON Schema

Fetch `/schema/<version>`, verify the digest from `/sha256/<version>`, and
validate documents with the local JSON-Schema implementation. Nim
(`starintel-doc.nim`), JS (`starintel_doc.js`), and CL (`star-cl`) all
consume the same artifact.

### Consumers that must not reach the network

Vendoring is always available: copy `schemas/starintel-doc-<v>.schema.json`
and `spec/star/starintel-core-<v>.star` from the canonical repository at the
reviewed commit, keep the digest from `spec/star/SHA256SUMS` next to them,
and verify locally. The HTTP service is a distribution channel, never a new
authority.

## Tests

```bash
python3 -m unittest tests.test_star_lang_export tests.test_spec_serving
```
