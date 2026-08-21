from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


DEFAULT_BUNDLE_LIMIT = 1_500_000_000
DEFAULT_SEARCH_SEGMENT_LIMIT = 16_000_000
DEFAULT_ORDINAL_CHUNK = 500_000


@dataclass(frozen=True)
class Segment:
    bundle: str
    offset: int
    length: int
    sha256: str

    def as_json(self) -> dict[str, Any]:
        return {
            "bundle": self.bundle,
            "offset": self.offset,
            "length": self.length,
            "sha256": self.sha256,
        }


class BundleWriter:
    def __init__(self, root: Path, stem: str, limit: int) -> None:
        self.root = root
        self.stem = stem
        self.limit = limit
        self.index = -1
        self.size = 0
        self.stream = None
        self.bundle_names: list[str] = []

    def _open(self) -> None:
        self.index += 1
        name = f"{self.stem}-{self.index:04d}.bundle"
        path = self.root / name
        self.stream = path.open("wb")
        self.size = 0
        self.bundle_names.append(name)

    def _close(self) -> None:
        if self.stream is not None:
            self.stream.close()
            self.stream = None

    def append(self, payload: bytes) -> Segment:
        if len(payload) > self.limit:
            raise ValueError(
                f"single index segment exceeds bundle limit: {len(payload)} > {self.limit}"
            )
        if self.stream is None:
            self._open()
        elif self.size and self.size + len(payload) > self.limit:
            self._close()
            self._open()
        assert self.stream is not None
        offset = self.size
        self.stream.write(payload)
        self.size += len(payload)
        return Segment(
            bundle=self.bundle_names[-1],
            offset=offset,
            length=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
        )

    def finish(self) -> list[str]:
        self._close()
        return list(self.bundle_names)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_metadata(root: Path, names: Iterable[str], base_url: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in names:
        path = root / name
        result[name] = {
            "url": f"{base_url.rstrip('/')}/{name}",
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compact_json_bytes(value) + b"\n")


def search_scope_payloads(
    scope: str,
    ordinals: list[int],
    segment_limit: int,
    ordinal_chunk: int = DEFAULT_ORDINAL_CHUNK,
) -> Iterator[bytes]:
    start = 0
    while start < len(ordinals):
        width = min(ordinal_chunk, len(ordinals) - start)
        while True:
            end = start + width
            payload = compact_json_bytes({scope: ordinals[start:end]})
            if len(payload) <= segment_limit:
                yield payload
                start = end
                break
            if width <= 1:
                raise ValueError(
                    f"search posting for scope {scope!r} cannot fit in {segment_limit} bytes"
                )
            width = max(1, width // 2)


def rewrite_search_metadata(site: Path, config: dict[str, Any], description: str) -> None:
    write_json(site / "search-index.json", config)

    for manifest_path in site.glob("*/downloads/dataset-manifest.json"):
        manifest = load_json(manifest_path)
        manifest["search"] = {
            "mode": config["format"],
            "minimum_query_characters": config["minimum_query_characters"],
            "manifest": "../../search-index.json",
        }
        write_json(manifest_path, manifest)

    for html_path in site.glob("*/documents.html"):
        markup = html_path.read_text(encoding="utf-8")
        markup = markup.replace(
            "Search uses compact canonical metadata shards, never raw corpus payloads.",
            description,
        )
        markup = markup.replace(
            "Search loads bounded byte ranges from immutable canonical metadata bundles, never raw corpus payloads.",
            description,
        )
        html_path.write_text(markup, encoding="utf-8")

    root_search = site / "search.html"
    if root_search.is_file():
        markup = root_search.read_text(encoding="utf-8")
        markup = markup.replace(
            "The browser loads one compact token-prefix shard and only the canonical metadata pages needed for matching records.",
            description,
        )
        markup = markup.replace(
            "The browser loads only bounded byte ranges needed from immutable search and canonical metadata bundles.",
            description,
        )
        root_search.write_text(markup, encoding="utf-8")


def source_index_roots(site: Path) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    indexes = site / "indexes"
    record_root = indexes / "records"
    search_root = indexes / "search"
    record_manifest_path = record_root / "manifest.json"
    search_manifest_path = search_root / "manifest.json"
    if not record_manifest_path.is_file() or not search_manifest_path.is_file():
        raise FileNotFoundError("generated record/search index manifests are missing")
    return (
        record_root,
        search_root,
        load_json(record_manifest_path),
        load_json(search_manifest_path),
    )


def externalize_release_ranges(
    site: Path,
    bulk: Path,
    base_url: str,
    bundle_limit: int,
    search_segment_limit: int,
) -> dict[str, Any]:
    record_root, search_root, record_manifest, search_manifest = source_index_roots(site)
    bulk_index_root = bulk / "indexes"
    if bulk_index_root.exists():
        shutil.rmtree(bulk_index_root)
    bulk_index_root.mkdir(parents=True)

    record_writer = BundleWriter(
        bulk_index_root, "starintel-record-index", bundle_limit
    )
    record_segments: list[dict[str, Any]] = []
    record_pages = sorted(record_root.glob("page-*.json"))
    expected_pages = int(record_manifest.get("page_count", 0))
    if expected_pages != len(record_pages):
        raise ValueError(
            f"record page count mismatch: manifest={expected_pages} files={len(record_pages)}"
        )
    for page in record_pages:
        payload = page.read_bytes()
        rows = json.loads(payload)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"record metadata page must be a non-empty array: {page}")
        segment = record_writer.append(payload).as_json()
        segment["first_id"] = str(rows[0][1])
        segment["last_id"] = str(rows[-1][1])
        record_segments.append(segment)
    record_bundles = record_writer.finish()

    search_writer = BundleWriter(
        bulk_index_root, "starintel-search-index", bundle_limit
    )
    search_segments: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(search_root.glob("*.json")):
        if path.name == "manifest.json":
            continue
        prefix = path.stem
        shard = load_json(path)
        if not isinstance(shard, dict):
            raise ValueError(f"search shard must be an object: {path}")
        segments: list[dict[str, Any]] = []
        for scope in sorted(shard):
            ordinals = shard[scope]
            if not isinstance(ordinals, list):
                raise ValueError(f"search postings must be arrays: {path}:{scope}")
            if not ordinals:
                continue
            for payload in search_scope_payloads(
                scope, ordinals, search_segment_limit
            ):
                segment = search_writer.append(payload).as_json()
                segment["scope"] = scope
                segments.append(segment)
        search_segments[prefix] = segments
    search_bundles = search_writer.finish()

    configured_prefixes = search_manifest.get("prefixes", [])
    if set(configured_prefixes) != set(search_segments):
        raise ValueError("search prefix manifest does not match emitted search shards")

    config = {
        "format": "starintel-release-range-index-v1",
        "record_count": int(record_manifest["record_count"]),
        "minimum_query_characters": int(
            search_manifest.get("minimum_query_characters", 2)
        ),
        "search": {
            "prefix_length": 2,
            "max_segment_bytes": search_segment_limit,
            "bundles": bundle_metadata(
                bulk_index_root, search_bundles, base_url
            ),
            "segments": search_segments,
        },
        "records": {
            "page_size": int(record_manifest["page_size"]),
            "page_count": len(record_segments),
            "fields": record_manifest.get("fields", []),
            "sorted_by": "id",
            "bundles": bundle_metadata(
                bulk_index_root, record_bundles, base_url
            ),
            "pages": record_segments,
        },
    }
    rewrite_search_metadata(
        site,
        config,
        "Search loads bounded byte ranges from immutable canonical metadata bundles, never raw corpus payloads.",
    )
    shutil.rmtree(site / "indexes")
    return config


def materialize_pages_static(
    site: Path,
    search_segment_limit: int,
) -> dict[str, Any]:
    record_root, search_root, record_manifest, search_manifest = source_index_roots(site)
    temporary_root = site / ".pages-search-index"
    if temporary_root.exists():
        shutil.rmtree(temporary_root)
    static_records = temporary_root / "records"
    static_search = temporary_root / "search"
    static_records.mkdir(parents=True)
    static_search.mkdir(parents=True)

    record_segments: list[dict[str, Any]] = []
    record_pages = sorted(record_root.glob("page-*.json"))
    expected_pages = int(record_manifest.get("page_count", 0))
    if expected_pages != len(record_pages):
        raise ValueError(
            f"record page count mismatch: manifest={expected_pages} files={len(record_pages)}"
        )
    for page in record_pages:
        payload = page.read_bytes()
        rows = json.loads(payload)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"record metadata page must be a non-empty array: {page}")
        destination = static_records / page.name
        destination.write_bytes(payload)
        record_segments.append(
            {
                "url": f"indexes/records/{page.name}",
                "length": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "first_id": str(rows[0][1]),
                "last_id": str(rows[-1][1]),
            }
        )

    search_segments: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(search_root.glob("*.json")):
        if path.name == "manifest.json":
            continue
        prefix = path.stem
        shard = load_json(path)
        if not isinstance(shard, dict):
            raise ValueError(f"search shard must be an object: {path}")
        segments: list[dict[str, Any]] = []
        segment_index = 0
        for scope in sorted(shard):
            ordinals = shard[scope]
            if not isinstance(ordinals, list):
                raise ValueError(f"search postings must be arrays: {path}:{scope}")
            if not ordinals:
                continue
            for payload in search_scope_payloads(
                scope, ordinals, search_segment_limit
            ):
                name = f"{prefix}-{segment_index:05d}.json"
                destination = static_search / name
                destination.write_bytes(payload)
                segments.append(
                    {
                        "url": f"indexes/search/{name}",
                        "length": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "scope": scope,
                    }
                )
                segment_index += 1
        search_segments[prefix] = segments

    configured_prefixes = search_manifest.get("prefixes", [])
    if set(configured_prefixes) != set(search_segments):
        raise ValueError("search prefix manifest does not match emitted search shards")

    config = {
        "format": "starintel-pages-static-index-v1",
        "record_count": int(record_manifest["record_count"]),
        "minimum_query_characters": int(
            search_manifest.get("minimum_query_characters", 2)
        ),
        "search": {
            "prefix_length": 2,
            "max_segment_bytes": search_segment_limit,
            "segments": search_segments,
        },
        "records": {
            "page_size": int(record_manifest["page_size"]),
            "page_count": len(record_segments),
            "fields": record_manifest.get("fields", []),
            "sorted_by": "id",
            "pages": record_segments,
        },
    }

    shutil.rmtree(site / "indexes")
    temporary_root.rename(site / "indexes")
    rewrite_search_metadata(
        site,
        config,
        "Search loads bounded same-origin metadata segments from this site, never raw corpus payloads.",
    )
    return config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare bounded StarIntel browser indexes for Pages or external range transport"
    )
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--bulk", type=Path)
    parser.add_argument("--base-url")
    parser.add_argument(
        "--transport",
        choices=("release-range", "pages-static"),
        default="release-range",
    )
    parser.add_argument(
        "--bundle-limit", type=int, default=DEFAULT_BUNDLE_LIMIT
    )
    parser.add_argument(
        "--search-segment-limit",
        type=int,
        default=DEFAULT_SEARCH_SEGMENT_LIMIT,
    )
    args = parser.parse_args()

    if args.transport == "pages-static":
        config = materialize_pages_static(args.site, args.search_segment_limit)
    else:
        if args.bulk is None or not args.base_url:
            parser.error("release-range transport requires --bulk and --base-url")
        config = externalize_release_ranges(
            args.site,
            args.bulk,
            args.base_url,
            args.bundle_limit,
            args.search_segment_limit,
        )

    search_segment_count = sum(
        len(segments) for segments in config["search"]["segments"].values()
    )
    print(
        f"index_transport={config['format']} "
        f"records={config['record_count']} "
        f"record_pages={config['records']['page_count']} "
        f"search_segments={search_segment_count} "
        f"max_search_segment_bytes={config['search']['max_segment_bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
