# StarIntel v0.9.0 conformance

This directory is the shared, versioned conformance source for the StarIntel language bindings.

This directory is the frozen legacy Auto-Dig conformance harness for the
snake-case corpus format. It does not define canonical StarIntel. Star-Lang is
the authority, and current language bindings consume the exact commit pinned by
`schema/starintel-schema.lock.json`. New cross-language conformance belongs to
the Star-Lang compatibility fixtures and each binding's generated adapter.

## Adapter protocol

Each adapter reads one JSON request from stdin and writes one JSON response to stdout. Diagnostics go to stderr.

Commands:

- `validate`
- `normalize`
- `roundtrip`
- `version`
- `capabilities`
- `schema-inventory`

Exit codes:

- `0`: success
- `1`: document rejected
- `2`: adapter/runtime failure
- `3`: unsupported specification version

## Run

```sh
./bin/conformance test \
  --adapter 'python=python ../starintel-python/starintel_doc/conformance_adapter.py' \
  --adapter 'js=node ../starintel-js/bin/starintel-conformance.js' \
  --adapter 'cl=sbcl --script ../starintel-cl/bin/starintel-conformance.lisp' \
  --adapter 'nim=../starintel-nim/starintel_conformance'

./bin/conformance test --producer cl --consumer nim
./bin/conformance test --fixture person.full.v1
./bin/conformance matrix --adapter 'python=...'
./bin/conformance report --format json
./bin/conformance dump-fixtures --output artifacts/fixtures-v0.9.0.json
```

The full run fails when any required adapter is absent, any ordered pair is skipped, any valid fixture mutates, any invalid fixture is accepted or categorized differently, dtype coverage is incomplete, or schema inventories disagree.

## Matrix semantics

Every direction runs independently. `cl -> js` does not imply `js -> cl`. Self-pairs are deterministic producer/consumer round trips, not unit-test shortcuts.

The comparison is semantic and type-sensitive. Object key order and whitespace are ignored. Missing versus null, integer versus number, array order, Unicode, unknown fields, and every added/removed/type-changed value are reported explicitly.
