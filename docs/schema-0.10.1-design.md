# StarIntel 0.10.1 Design and Decision Record

Status: implemented (branch `spec/0.10.1-unify`)
Date: 2026-09-19
Authority: this document records the decisions behind the StarIntel 0.10.1
release. The executable authority is `starintel_doc/spec.py`, the generated
`schemas/starintel-doc-v0.10.1.schema.json`, and
`schemas/starintel-doc-v0.10.1.manifest.json`, resolved through
`scripts/schema-release.py`.

## 1. Operator instruction and version normalization

Operator instruction received in chat on 2026-09-19, explicitly approving this
work: mint version **0.10.1**, unify the spec, YAGNI-declutter, flesh out the
`breach` dtype as DATA-LEAK support, and add network/wireless/pcap dtypes.

The operator wrote the target as `0.010.1`. That literal does not parse as a
semantic version in any StarIntel tooling (`scripts/schema-release.py`
`VERSION_RE`), and no StarIntel line has ever used a `0.0NN` minor. It was
canonicalized to **0.10.1**: the next minor line after the 0.9.x series, which
matches every other element of the instruction (mint a new base line, unify,
fold the 0.9.2 side-profile dtypes into core). This interpretation is recorded
here per the instruction's own requirement.

## 2. Relationship to the 0.9 line and the unbumped 0.9.2 core plan

State before this release (verified 2026-09-19 via
`scripts/schema-release.py current`):

- active release/profile `0.9.1` over immutable base schema `0.9.0`
  (51 dtypes including the transitional `operation` dtype);
- `starintel_doc/spec_092.py` layered `http-transaction` + `web-capture` over
  the base with `RELEASE_VERSION = 0.9.2`, published only as the side profile
  manifest `schemas/starintel-network-capture-v0.9.2.manifest.json`;
- the **core** release was never bumped to 0.9.2; the planned 0.9.2 core bump
  is therefore superseded by this release.

Decisions:

1. **0.10.1 supersedes the unbumped 0.9.2 core plan.** The two network-capture
   dtypes fold into the 0.10.1 core `TYPE_FIELDS` verbatim (same fields, same
   requireds, same aliases; see §5.3).
2. `schemas/starintel-network-capture-v0.9.2.manifest.json` remains on disk as
   a historical record and is marked superseded by the 0.10.1 manifest's
   `legacy` block. It is not deleted.
3. All `schemas/starintel-doc-v0.9.0.*` artifacts (schema, manifest, expansion
   registry) remain on disk, untouched, for consumers still pinned to 0.9.
4. `starintel_doc/spec_092.py` is retained as a compatibility module for
   0.9-line consumers and is not deleted. Its public surface
   (`SCHEMA_VERSION`, `RELEASE_VERSION`, `PROFILE_ID`,
   `HTTP_TRANSACTION_FIELDS`, `WEB_CAPTURE_FIELDS`, `TYPE_FIELDS`,
   `REQUIRED_DATA_FIELDS`, `DTYPE_ALIASES`, `document_schema`, `data_schema`)
   keeps working. Minimal coherent changes made to it:
   - `SCHEMA_VERSION` is pinned to the literal `"0.9.0"` instead of aliasing
     `base.SCHEMA_VERSION` (which is now `"0.10.1"`), and its
     `COMMON_PROPERTIES` pin `schema_version` to the `"0.9.0"` const, so the
     legacy profile stays a strict 0.9 validator.
   - its field tables re-export the base tables. The 0.9.2 profile therefore
     now tracks the unified vocabulary as a superset. Consumers who need the
     exact frozen 0.9-era profile must pin the 0.9.x git tag or the legacy
     schema artifacts; the repo no longer carries a second frozen field table
     (that duplication is exactly what this release removes).

## 3. Unify decision: one vocabulary authority

Before 0.10.1 there were two vocabularies:

- the **wire authority**: `starintel_doc/spec.py` `TYPE_FIELDS` (51 dtypes),
  consumed by the validators, the emitters, and the generated
  `schemas/starintel-doc-v0.9.0.schema.json`;
- the **expansion registry**: `schemas/starintel-doc-v0.9.0.expansion.json`,
  a richer per-dtype profile vocabulary (`dtype_fields`, `common_data_fields`,
   `field_kinds`, lineage/provenance/verification/top-level field lists) that
  diverged from the wire fields and was only consumed by a dtype-name parity
  test (`tests/test_operation_registry.py`). Its fields were never
  materialized into the generated schema, so no validatable document could
  ever carry them — confirmed empirically: 0 occurrences of any of the 442
  distinct expansion field names in 28,577 corpus files under `db/` and
  `digs/` (counted 2026-09-19; `usage` evidence summarized in §4).

Decision: **the expansion vocabulary merges into the wire spec.** From 0.10.1
there is exactly one authority: `starintel_doc/spec.py` plus the generated
JSON Schema. Concretely:

- `EXPANSION_ABSORBED_FIELDS` in `spec.py` now carries, as explicit literal
  field tables, every absorbed expansion field per dtype, merged into
  `TYPE_FIELDS` at import time (mirroring the existing
  `install_operation_spec()` precedent for import-time table extension).
- Four common data fields with wire precedent and real corpus usage
  (`description`, `status`, `valid_from`, `valid_to`) are absorbed into every
  dtype (`ABSORBED_COMMON_DATA_FIELDS`).
- The kind mapping from the registry's `field_kinds` to JSON Schema kinds:

  | registry kind | wire kind |
  |---|---|
  | `string_array` | `STRS` |
  | `reference_array` | `STRS` (wire form: arrays of referenced document `_id` strings) |
  | `identifier_array` | `array(IDENTIFIER)` (identifier records `{scheme, value, ...}`) |
  | `boolean` | `BOOL` |
  | `integer` | `INT` |
  | `number` | `NUM` |
  | `score` | `SCORE` (0..1) |
  | `money` | `MONEY` object `{amount, currency, basis, as_of, notes}` |
  | `money_array` | `array(MONEY)` |
  | `facet_array`, `action_array`, `role_array` | `array(JSON_MAP)` |
  | `json` | `JSON_VALUE` |
  | `announced_by_asns` (`integer[]`) | `array(INT)` |
  | `coordinates` (`number[]`) | `array(NUM)` |
  | `hashes` (`stringMap`) | `JSON_MAP` (algorithm → digest) |

- Unclassified scalar names infer their kind by suffix: `*_ids` → `STRS`,
  `*_id` → `STR`, `*_at` → `NULLABLE_DATE_TIME`, `*_url`/`*_uri` → `STR`,
  otherwise `STR`.

### Materialized typed structs

The registry's `field_kinds.typed` struct arrays with network relevance are
materialized as JSON-kind fields whose inner shape is documented here:

- `host.interface_records`: array of networkInterface records
  `{name?, mac?, ipv4?, ipv6?, mtu?, type?, vendor?}` (free-form object map;
  keys beyond a documented core are permitted because the field is
  `array(JSON_MAP)`).
- `host.service_records`: array of networkService records
  `{port?, protocol?, service?, product?, version?, banner?}`.
- `host.certificate_records`: array of certificate records
  `{sha256_fingerprint?, serial?, issuer?, subject?, not_before?, not_after?,
  key_algorithm?}`.
- `url.http_exchanges`: array of httpExchange records
  `{method?, url?, status?, request_headers?, response_headers?,
  started_at?, duration_ms?}`.
- `domain` DNS records: already materialized in the 0.9 wire as
  `domain.dns_records` (`array(JSON_MAP)` of
  `{name?, type?, ttl?, value?}` records); the registry's duplicate name
  `dns_record_entries` is not added.

## 4. YAGNI declutter log (evidence-based)

Rule applied: check usage with exact-name search across the corpus (`db/`
`*.ndjson` + `digs/**/starintel-documents.jsonl`, 28,577 files) and the
binding repositories before dropping; when uncertain, KEEP and record. The
binding repositories (`lost-rob0t/starintel-doc`, `starintel_doc.js`,
`star-cl`, `starintel-doc.nim`) validate against the generated wire schema,
which never contained expansion vocabulary, so binding usage of these names is
structurally impossible; the local Nim checkout (`.starintel-doc-nim`) was
searched as a spot check (0 hits).

Dropped (0 corpus occurrences each; never validatable pre-0.10.1):

| dropped name | reason |
|---|---|
| `status_history`, `facets`, `external_references`, `role_assignments`, `attributes`, `canonical_key`, `display_label`, `reference_ids`, `source_record_ids`, `evidence_record_ids`, `object_marking_ids`, `supersedes_ids`, `superseded_by_ids` | common data fields with zero usage; several duplicate envelope machinery (`lineage.supersedes`/`superseded_by`, `attachments`, `extensions`) that already exists |
| `measurement` (observation), `query_plan` (target/investigation-target/research-pass) | typed structs, zero usage, no wire precedent |
| `dns_record_entries`, `docket_entry_records`, `file_records`, `finding_records`, `modification_records`, `reaction_records` | typed-struct names that duplicate existing wire fields (`domain.dns_records`, `legal-case.docket_entries`, `dataset-manifest.files`, `analysis/research-pass.findings`, `contract.modifications`, `message.reactions`) — the wire name wins, no duplicate alias added |
| `quoted_post_id` (social-media-post) | exact duplicate of existing wire `quote_post_id` |

Kept despite zero usage (uncertainty rule and/or explicit instruction):

- the full per-dtype scalar/string/reference absorption (§3) — kept because the
  unify decision makes the declared profile vocabulary real wire vocabulary;
  producers may start using it without a spec change;
- `announced_by_asns`, `coordinates`, `hashes` (typed-but-simple, explicit
  instruction or existing wire precedent);
- the four absorbed common data fields (`description`, `status`, `valid_from`,
  `valid_to`) — wire precedent (envelope + `IDENTIFIER`) and corpus usage;
- every pre-existing 0.9 wire field — none dropped; 0.10.1 is
  additive-with-migration, so dropping wire fields would break 0.9 consumers.

Also retired as authority (not deleted): the expansion registry itself
(`schemas/starintel-doc-v0.9.0.expansion.json`) — frozen as a 0.9-line legacy
artifact; the 0.10.1 manifest carries no `expansion_registry_path` and
`scripts/schema-release.py` treats its absence as the unified-line marker.

## 5. New dtypes and enum vocabulary

### 5.1 Shared device-class vocabulary

`DEVICE_CLASS_VALUES` is a shared enum reused by `host.device_class` and
`network-device.device_class`:

`other, unknown, general-purpose, router, broadband-router, switch, wap,
bridge, firewall, load-balancer, proxy-server, print-server,
terminal-server, terminal, phone, voip-phone, voip-adapter, pbx, webcam,
printer, media-device, game-console, pda, storage, storage-misc,
power-device, remote-management, security-misc, specialized, telecom-misc,
iot`

Provenance: anchored to the nmap-os-db device-class vocabulary (nmap's
`fingerprint DB` `CPE`/device-class hints, the same taxonomy used by nmap
`-O` output and derived tooling), kept as a closed enum so OS-fingerprint
importers share one scale. `host` keeps its free-string `device_type` for
legacy data.

`host` additionally gains `device_class_source` (how the class was derived,
e.g. `nmap-os-db`, `manual`) and `device_class_evidence` (the observation
backing the classification).

### 5.2 New dtypes

All added to core `TYPE_FIELDS` with requireds in
`REQUIRED_DATA_FIELDS`; full field lists are executable in
`starintel_doc/spec.py` and the generated schema.

- **`network-device`** (requires `device_class`): physical/virtual network
  infrastructure entity; `hardware_class` enum
  `[unknown, chassis, backplane, container, power-supply, fan, sensor, module,
  port, stack, cpu, energy-object, battery, storage-drive, other]`
  (ENTITY-MIB `PhysicalClass` anchored). Alias `network_device`.
- **`pcap-capture`** (requires `capture_id`, `file_uri`, `file_sha256`):
  a packet-capture artifact record; `format` enum `[pcap, pcapng, unknown]`.
  Raw packets are never inline: `file_uri` + `file_sha256` are the artifact
  reference (same posture as §6).
- **`network-conversation`** (requires `conversation_id`, `capture_id`,
  `layer`): a layer-scoped conversation between two endpoints inside one
  capture; `layer` enum `[eth, ip, ipv6, tcp, udp]`; endpoint objects are
  `{host_id?, mac?, ipv4?, ipv6?, port?}`; `protocols` lists IANA service
  names outer→inner per STIX 2.1 `network-traffic:protocols`.
- **`wireless-network`** (requires `bssid`, `security`): an observed wireless
  network (Wigle/Kismet-shaped); `security` enum `[open, wep, wpa-psk,
  wpa2-psk, wpa2-enterprise, wpa3-psk, wpa3-enterprise, wpa2wpa3-psk,
  unknown]`; `band` enum `[2.4ghz, 5ghz, 6ghz, unknown]`; `source_network_id`
  carries the Wigle netid / Kismet device key.
- **`wireless-station`** (requires `mac`): an observed wireless client/AP
  station; `station_type` enum `[station, ap, bridge, bridge-ap, unknown]`;
  `source_device_id` carries the Kismet key.

### 5.3 Folded 0.9.2 profile dtypes

`http-transaction` (requires `transaction_id`, `method`, `url`,
`response_status`) and `web-capture` (requires `capture_id`, `url`,
`screenshot_uri`, `screenshot_hash`) enter core `TYPE_FIELDS` with exactly the
fields and requireds from `starintel_doc/spec_092.py`, including the captcha
context fields, redaction bookkeeping, and artifact-reference-only body
policy. Aliases `http_transaction`, `web_capture` move into the base
`DTYPE_ALIASES` (and remain in `spec_092`).

### 5.4 Absorptions on existing dtypes (explicit instruction)

- `host` gains `device_class` (+source/evidence) and absorbs `host_type`,
  `interface_records`, `service_records`, `certificate_records`,
  `software_ids`, `cloud_account_ids`, `virtualization_type`,
  `parent_host_id`, `observed_by_ids`.
- `network` absorbs `network_type`, `prefixes`, `allocation_id`,
  `registrant_id`, `contact_ids`, `routing_policy`, `bgp_observation_ids`,
  `announced_by_asns` (`array(INT)`), `rpki_status`.

## 6. Breach as DATA-LEAK support

`breach` becomes the dtype for data-breach/data-leak intelligence. `name`
becomes required (`REQUIRED_DATA_FIELDS["breach"] = ("name",)` — note: today's
0.9 wire has **no** required breach fields; the operator work item said
"name stays required as today", which describes the intended state, so the
required is introduced now; the db corpus contains zero `breach` documents,
so nothing existing can break). All other new fields are optional:

- `leak_type` enum `[data-breach, data-leak, accidental-exposure,
  ransomware-exfiltration, insider-leak, combo-list, scraping-aggregation,
  unknown]`;
- timeline: `incident_date_start`, `incident_date_end`, `discovery_date`,
  `disclosed_date`, `published_date` (nullable date-times; the legacy
  `breached_at`/`discovered_at` remain valid);
- content characterization: `data_categories` (string array whose items are
  constrained to `[credentials, email-addresses, password-hash,
  password-plaintext, pii, financial, payment-card, health, source-code,
  internal-documents, database-dumps, session-tokens, api-keys, private-keys,
  geolocation, authentication-cookies, other]`), `records_affected` (INT),
  `record_count_basis` enum `[operator-reported, sample-extrapolated, exact,
  unknown]`, `sample_size` (INT);
- credential metrics: `credential_count`, `unique_email_count`,
  `plaintext_password_count` (INT), `hash_algorithms` (STRS);
- corpus reference: `leaked_file_ids` (STRS, refs to `file` docs),
  `leak_corpus_uri`, `leak_corpus_sha256`;
- `distribution_observations`: array of
  `{platform?, url?, actor_handle?, first_seen?, last_seen?}` objects;
- scope/attribution: `affected_org_ids`, `affected_domain_ids` (STRS),
  `affected_person_count` (INT), `initial_access_vector`, `root_cause`,
  `cve_ids`, `threat_actor_ids`, `malware_families`;
- epistemics: `corroboration` enum `[single-source-unverified, multi-source,
  officially-confirmed, disputed, unknown]`, `hibp_breach_name`,
  `regulator_filing_refs` (STRS).

### Security posture: reference-only leaked material

**RAW leaked material (credential dumps, PII rows, combo lists, plaintext
passwords) is never stored inline in a breach document.** Only counts,
hashes, category labels, and artifact references (`leaked_file_ids`,
`leak_corpus_uri` + `leak_corpus_sha256`) are representable. This follows the
0.9.2 network-capture precedent (`starintel-network-capture-v0.9.2.manifest.json`
`security.artifact_reference_only` for request/response bodies, screenshots,
and DOM) and generalizes it to leaked corpora.

Enforcement: `data` has `additionalProperties: false`, and no breach field is
a raw-bytes field, so the shape itself cannot carry leaked material. As a
fail-closed guard for future edits, `starintel_doc/validation.py` rejects any
breach document whose `data` contains a forbidden inline field name
(`BREACH_FORBIDDEN_INLINE_FIELDS`: `raw_records`, `leaked_records`,
`credentials`, `credential_dump`, `password_dump`, `plaintext_records`,
`raw_content`, `dump_content`, `leak_content`, `records_inline`). Any future
proposal to add an inline credential-material field must be rejected in
review; if such a field is ever legitimately needed it must go through a
revision of this decision record. (Content-scanning of
`distribution_observations`/text fields for raw password strings is
explicitly out of scope; `leak_corpus_uri` is reference-only by shape.)

## 7. schema_version migration

- `SCHEMA_VERSION = "0.10.1"`; emitters (`Document.create`,
  `network_capture` excluded — it stays 0.9) write `"0.10.1"`.
- `ACCEPTED_SCHEMA_VERSIONS = {"0.9.0", "0.10.1"}`; `validate_document`
  accepts either during the migration window; the generated schema's envelope
  `schema_version` becomes `{"enum": ["0.9.0", "0.10.1"]}`.
- Legacy `0.9.0` documents remain valid as-is; a future migrator
  (`migrate-starintel-v0.10` style, following the
  `scripts/migrate-starintel-v0.9.py` pattern) will upgrade legacy docs and
  record migration provenance; it is intentionally not part of this release —
  the corpus keeps validating under dual acceptance.
- Compatibility label: `additive-with-migration-v0.10`.

## 8. Mint tooling

`scripts/schema-release.py` gains a `mint --to <X.Y.Z>` subcommand. Mint
creates a **new base line** (as opposed to `bump`, which only advances the
next patch of the current line). For 0.10.1 it:

1. refuses unless the target parses, strictly advances the current base
   schema version, the current line passes `check()`, and
   `starintel_doc.spec.SCHEMA_VERSION` already equals the target (spec source
   lands first; mint does artifact/metadata plumbing only);
2. regenerates `schemas/starintel-doc-v0.10.1.schema.json` through the
   existing generator (`scripts/starintel.py schema --output ...`), verifying
   the generated dtype enum and `schema_version` enum against the package;
3. writes `schemas/starintel-doc-v0.10.1.manifest.json`
   (`schema_version`/`release_version`/`profile_version` `0.10.1`,
   `schema_revision` `0.10.1+fields.20260919.1`, compatibility
   `additive-with-migration-v0.10`, computed `dtype_count`, `legacy` and
   `migration` blocks);
4. rewrites its own module constants (active `MANIFEST` path; the expansion
   constant becomes `LEGACY_EXPANSION` since unified lines have no active
   expansion registry);
5. updates `conformance/implementations.json` (authority fields
   `spec_version`, `release_version`, `release_contract.wire_spec_version`,
   `release_contract.release_version`, compatibility, plus a `migration`
   note; per-binding `library_release`/`supported_spec_versions` are left for
   the binding repositories' own sync workflows, per existing `bump` policy),
   `conformance/__init__.py`, `starintel_auto_dig.nimble`,
   `tests/test_operation_registry.py`, and `conformance/fixtures.py`;
6. repoints the current-schema filename pins
   (`scripts/validate-for-merge.py`, `scripts/starintel_validate.nim`,
   `.github/workflows/sync-schema.yml`, `.github/workflows/conformance.yml`)
   from the 0.9.0 schema file to the 0.10.1 file;
7. re-runs `check()` and fails unless the minted line is consistent.

`check()` is line-agnostic: expansion-registry validation applies only when
the active manifest declares `expansion_registry_path` (0.9 line); unified
lines instead require their `base_schema_path` to exist.
`pyproject.toml`'s package version is intentionally untouched (it was never
release-tooling-governed; recorded here to preempt "why not" questions).

## 9. star-lang bootstrap staging

0.10.1 remains a **JSON authority** release: `spec.py` + generated JSON
Schema. star-lang becomes the source of truth later, via a JSON-Schema
emitter emitted from star-lang spec artifacts. The first star-lang spec
artifact of this program is the `star-relations` library
(`~/starintel/star-relations`, `spec/starintel-relations.star`,
`org.starintel/relations@1` v1.0.0), a declarative relation taxonomy whose
"live vocabulary" predicate names are frozen to the production DB.

Known gaps before star-lang can hold authority (why staging, not switching):

- no JSON-Schema emitter exists in star-lang yet;
- `pattern`/`format` constraints are not enforced by the star-lang checker;
- the compile path is a single-actor CLI (no multi-actor/library build
  pipeline);
  the star-lang IR drops StarIntel document metadata (envelope fields do not
  survive lowering);
- exact-version imports depend on placeholder digests
  (`org.starintel/core@1` is unpublished; `star-relations` carries thin
  markers and a digest sidecar instead).

## 10. Decision log (chronological, incl. mid-work calls)

1. `0.010.1` → `0.10.1` normalization (§1).
2. 0.9.2 core plan superseded; side-profile manifest kept as historical
   record (§2).
3. Expansion registry retired as an authority; vocabulary absorbed into
   `spec.py` as explicit literal tables merged at import (§3); registry file
   frozen as legacy.
4. Declutter drops per evidence table (§4); uncertainty rule applied as
   keep-and-record.
5. `breach.name` made required, resolving the instruction's "stays required
   as today" against the actual 0.9 state (no requireds; zero corpus breach
   docs) (§6).
6. `data_categories` items are enum-constrained (with `other` as the escape
   hatch) rather than free strings — the instruction's "from [...]" read as a
   closed vocabulary.
7. pcap/conversation JSON fields (`interfaces`, `protocol_hierarchy`,
   endpoints, `distribution_observations`) are materialized as typed
   object/array-of-object schemas rather than opaque `JSON_VALUE`, because
   the instruction documents their inner shapes exactly; broader struct
   arrays from the old registry stay `array(JSON_MAP)`.
8. `spec_092.SCHEMA_VERSION` pinned to literal `"0.9.0"` (base alias now says
   `0.10.1`) so the legacy profile remains a strict 0.9 validator (§2).
9. Release-coupling tests (`tests/test_operation_registry.py` inventory
   assertions, new artifact-currency tests) go red between the spec commit
   and the mint commit by construction; the branch HEAD is the green state.
10. Nim merge gate (`nimble buildFast && bin/validate-for-merge --site`) is
    **pending for the human**: the corpus-wide strict validation and site
    build were not run in this change (per instruction); the gate now points
    at the 0.10.1 schema file. Risk noted in §11.

## 11. Open risks

- **Nim merge gate not run** (pending human): the Nim validator now consumes
  the 0.10.1 schema whose envelope `schema_version` is an enum, not a const;
  if the Nim codegen assumed const semantics this surfaces at the gate, not
  here.
- Binding repositories must repin through their own lock/sync workflows
  before claiming 0.10.1; `implementations.json` deliberately does not flip
  their `supported_spec_versions`.
- The dual-version acceptance window is open-ended; a future migrator should
  close it.
- `db/` was not touched; corpus documents remain `0.9.0` and validate under
  dual acceptance.
