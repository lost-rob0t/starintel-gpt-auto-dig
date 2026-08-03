from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from .store import LocatedDocument, compact, iter_jsonl

SEAL_FORMAT = "starintel-evidence-seal"
PROOF_FORMAT = "starintel-evidence-proof"
FORMAT_VERSION = 1
HASH_ALGORITHM = "sha256"
TREE_ALGORITHM = "sha256-domain-separated-binary-merkle-v1"
LEAF_DOMAIN = b"STARINTEL-EVIDENCE-LEAF-V1\x00"
NODE_DOMAIN = b"STARINTEL-EVIDENCE-NODE-V1\x00"
EMPTY_DOMAIN = b"STARINTEL-EVIDENCE-EMPTY-V1\x00"


@dataclass(frozen=True, slots=True)
class EvidenceLeaf:
    entry: dict[str, Any]
    document_canonical: str
    digest: bytes


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _path_label(path: Path, root: Path | None) -> str:
    if root is not None:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            try:
                return path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                pass
    return path.as_posix()


def _leaf_entry(located: LocatedDocument, *, root: Path | None) -> tuple[dict[str, Any], str]:
    document = located.document
    canonical = compact(document)
    entry = {
        "_id": str(document.get("_id", "")),
        "dataset": str(document.get("dataset", "")),
        "document_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "dtype": str(document.get("dtype", "")),
        "line": int(located.line),
        "path": _path_label(located.path, root),
        "surface": str(located.surface),
    }
    return entry, canonical


def build_leaves(
    documents: Iterable[LocatedDocument], *, root: Path | None = None
) -> list[EvidenceLeaf]:
    staged: list[tuple[dict[str, Any], str]] = [
        _leaf_entry(located, root=root) for located in documents
    ]
    staged.sort(
        key=lambda item: (
            item[0]["surface"],
            item[0]["path"],
            item[0]["line"],
            item[0]["_id"],
            item[0]["document_sha256"],
        )
    )
    return [
        EvidenceLeaf(
            entry=entry,
            document_canonical=canonical,
            digest=_sha256(LEAF_DOMAIN + _canonical_json(entry).encode("utf-8")),
        )
        for entry, canonical in staged
    ]


def _next_level(level: list[bytes]) -> list[bytes]:
    if len(level) % 2:
        level = [*level, level[-1]]
    return [
        _sha256(NODE_DOMAIN + level[index] + level[index + 1])
        for index in range(0, len(level), 2)
    ]


def merkle_root(hashes: Iterable[bytes]) -> bytes:
    level = list(hashes)
    if not level:
        return _sha256(EMPTY_DOMAIN)
    while len(level) > 1:
        level = _next_level(level)
    return level[0]


def build_seal(
    documents: Iterable[LocatedDocument],
    *,
    root: Path | None = None,
    include_entries: bool = False,
    scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    leaves = build_leaves(documents, root=root)
    index_payload = "".join(_canonical_json(leaf.entry) + "\n" for leaf in leaves)
    counts_by_dtype = Counter(leaf.entry["dtype"] for leaf in leaves)
    counts_by_dataset = Counter(leaf.entry["dataset"] for leaf in leaves)
    counts_by_surface = Counter(leaf.entry["surface"] for leaf in leaves)
    receipt: dict[str, Any] = {
        "format": SEAL_FORMAT,
        "format_version": FORMAT_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "tree_algorithm": TREE_ALGORITHM,
        "leaf_count": len(leaves),
        "merkle_root_sha256": merkle_root(leaf.digest for leaf in leaves).hex(),
        "index_sha256": hashlib.sha256(index_payload.encode("utf-8")).hexdigest(),
        "counts_by_dtype": dict(sorted(counts_by_dtype.items())),
        "counts_by_dataset": dict(sorted(counts_by_dataset.items())),
        "counts_by_surface": dict(sorted(counts_by_surface.items())),
        "scope": dict(sorted((scope or {}).items())),
    }
    if include_entries:
        receipt["entries"] = [leaf.entry for leaf in leaves]
    return receipt


def iter_corpus_jsonl(path: Path, *, surface: str = "published-corpus") -> Iterator[LocatedDocument]:
    yield from iter_jsonl(path, surface=surface)


def build_corpus_seal(path: Path, *, include_entries: bool = False) -> dict[str, Any]:
    path = path.resolve()
    payload = path.read_bytes()
    receipt = build_seal(
        iter_corpus_jsonl(path),
        root=path.parent,
        include_entries=include_entries,
        scope={"kind": "jsonl", "path": path.name},
    )
    receipt["corpus_file_sha256"] = hashlib.sha256(payload).hexdigest()
    receipt["corpus_size_bytes"] = len(payload)
    return receipt


def _seal_comparison_fields(receipt: dict[str, Any]) -> tuple[str, ...]:
    fields = (
        "format",
        "format_version",
        "hash_algorithm",
        "tree_algorithm",
        "leaf_count",
        "merkle_root_sha256",
        "index_sha256",
        "counts_by_dtype",
        "counts_by_dataset",
        "counts_by_surface",
        "scope",
        "corpus_file_sha256",
        "corpus_size_bytes",
    )
    if "entries" in receipt:
        return (*fields, "entries")
    return fields


def verify_corpus_seal(path: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    actual = build_corpus_seal(path, include_entries="entries" in receipt)
    errors = [
        f"{field}: expected {receipt.get(field)!r}, got {actual.get(field)!r}"
        for field in _seal_comparison_fields(receipt)
        if receipt.get(field) != actual.get(field)
    ]
    return {"ok": not errors, "errors": errors, "actual": actual}


def _expected_proof_steps(leaf_count: int) -> int:
    steps = 0
    width = leaf_count
    while width > 1:
        width = (width + 1) // 2
        steps += 1
    return steps


def build_inclusion_proof(
    documents: Iterable[LocatedDocument],
    *,
    doc_id: str,
    root: Path | None = None,
    path: str = "",
) -> dict[str, Any]:
    leaves = build_leaves(documents, root=root)
    matches = [
        (index, leaf)
        for index, leaf in enumerate(leaves)
        if leaf.entry["_id"] == doc_id and (not path or leaf.entry["path"] == path)
    ]
    if not matches:
        raise ValueError(f"document not found: {doc_id!r}")
    if len(matches) > 1:
        locations = ", ".join(match.entry["path"] for _, match in matches)
        raise ValueError(
            f"document ID is present on multiple surfaces; pass an exact path: {locations}"
        )

    leaf_index, selected = matches[0]
    siblings: list[dict[str, str]] = []
    level = [leaf.digest for leaf in leaves]
    index = leaf_index
    while len(level) > 1:
        level_width = len(level)
        if level_width % 2:
            level = [*level, level[-1]]
        sibling_index = index - 1 if index % 2 else index + 1
        siblings.append(
            {
                "side": "left" if sibling_index < index else "right",
                "sha256": level[sibling_index].hex(),
            }
        )
        level = _next_level(level)
        index //= 2

    return {
        "format": PROOF_FORMAT,
        "format_version": FORMAT_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "tree_algorithm": TREE_ALGORITHM,
        "leaf_count": len(leaves),
        "leaf_index": leaf_index,
        "merkle_root_sha256": merkle_root(leaf.digest for leaf in leaves).hex(),
        "leaf": selected.entry,
        "document_canonical": selected.document_canonical,
        "siblings": siblings,
    }


def build_corpus_inclusion_proof(path: Path, doc_id: str) -> dict[str, Any]:
    path = path.resolve()
    return build_inclusion_proof(
        iter_corpus_jsonl(path),
        doc_id=doc_id,
        root=path.parent,
    )


def verify_inclusion_proof(
    proof: dict[str, Any], *, expected_root: str = ""
) -> dict[str, Any]:
    errors: list[str] = []
    if proof.get("format") != PROOF_FORMAT:
        errors.append(f"unsupported proof format: {proof.get('format')!r}")
    if proof.get("format_version") != FORMAT_VERSION:
        errors.append(f"unsupported proof version: {proof.get('format_version')!r}")
    if proof.get("hash_algorithm") != HASH_ALGORITHM:
        errors.append(f"unsupported hash algorithm: {proof.get('hash_algorithm')!r}")
    if proof.get("tree_algorithm") != TREE_ALGORITHM:
        errors.append(f"unsupported tree algorithm: {proof.get('tree_algorithm')!r}")
    if expected_root and proof.get("merkle_root_sha256") != expected_root:
        errors.append("proof is not anchored to the expected Merkle root")

    leaf = proof.get("leaf")
    canonical = proof.get("document_canonical")
    siblings = proof.get("siblings")
    if not isinstance(leaf, dict):
        errors.append("leaf must be an object")
    if not isinstance(canonical, str):
        errors.append("document_canonical must be a string")
    if not isinstance(siblings, list):
        errors.append("siblings must be a list")
    if errors:
        return {"ok": False, "errors": errors}

    try:
        document = json.loads(canonical)
    except json.JSONDecodeError as exc:
        return {"ok": False, "errors": [f"document_canonical is invalid JSON: {exc}"]}
    if not isinstance(document, dict):
        errors.append("document_canonical must encode a JSON object")
    elif compact(document) != canonical:
        errors.append("document_canonical is not canonical StarIntel JSON")

    if isinstance(document, dict):
        expected_document_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if leaf.get("document_sha256") != expected_document_hash:
            errors.append("document hash does not match leaf")
        for field in ("_id", "dataset", "dtype"):
            if str(document.get(field, "")) != str(leaf.get(field, "")):
                errors.append(f"document {field} does not match leaf")

    try:
        leaf_count = int(proof.get("leaf_count"))
        leaf_index = int(proof.get("leaf_index"))
    except (TypeError, ValueError):
        errors.append("leaf_count and leaf_index must be integers")
        return {"ok": False, "errors": errors}
    if leaf_count < 1:
        errors.append("leaf_count must be positive")
    if leaf_index < 0 or leaf_index >= leaf_count:
        errors.append("leaf_index is outside the tree")
    if len(siblings) != _expected_proof_steps(leaf_count):
        errors.append("proof has the wrong number of sibling steps")
    if errors:
        return {"ok": False, "errors": errors}

    current = _sha256(LEAF_DOMAIN + _canonical_json(leaf).encode("utf-8"))
    index = leaf_index
    width = leaf_count
    for step_number, step in enumerate(siblings, 1):
        if not isinstance(step, dict):
            errors.append(f"sibling step {step_number} must be an object")
            break
        side = step.get("side")
        raw_hash = step.get("sha256")
        try:
            sibling = bytes.fromhex(str(raw_hash))
        except ValueError:
            errors.append(f"sibling step {step_number} has invalid hexadecimal")
            break
        if len(sibling) != hashlib.sha256().digest_size:
            errors.append(f"sibling step {step_number} is not a SHA-256 digest")
            break

        duplicated_tail = width % 2 == 1 and index == width - 1
        expected_side = "right" if index % 2 == 0 else "left"
        if side != expected_side:
            errors.append(
                f"sibling step {step_number} has side {side!r}; expected {expected_side!r}"
            )
            break
        if duplicated_tail and sibling != current:
            errors.append(f"sibling step {step_number} must duplicate the odd tail node")
            break

        current = (
            _sha256(NODE_DOMAIN + sibling + current)
            if side == "left"
            else _sha256(NODE_DOMAIN + current + sibling)
        )
        index //= 2
        width = (width + 1) // 2

    if not errors and current.hex() != proof.get("merkle_root_sha256"):
        errors.append("computed Merkle root does not match proof")
    return {
        "ok": not errors,
        "errors": errors,
        "merkle_root_sha256": current.hex() if not errors else "",
    }
