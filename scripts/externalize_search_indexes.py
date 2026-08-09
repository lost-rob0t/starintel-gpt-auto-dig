from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_BUNDLE_LIMIT = 1_500_000_000


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


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def externalize(site: Path, bulk: Path, base_url: str, bundle_limit: int) -> dict[str, Any]:
    indexes = site / "indexes"
    record_root = indexes / "records"
    search_root = indexes / "search"
    record_manifest_path = record_root / "manifest.json"
    search_manifest_path = search_root / "manifest.json"
    if not record_manifest_path.is_file() or not search_manifest_path.is_file():
        raise FileNotFoundError("generated record/search index manifests are missing")

    record_manifest = load_json(record_manifest_path)
    search_manifest = load_json(search_manifest_path)
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
        segment = record_writer.append(page.read_bytes())
        record_segments.append(segment.as_json())
    record_bundles = record_writer.finish()

    search_writer = BundleWriter(
        bulk_index_root, "starintel-search-index", bundle_limit
    )
    search_segments: dict[str, dict[str, Any]] = {}
    for path in sorted(search_root.glob("*.json")):
        if path.name == "manifest.json":
            continue
        prefix = path.stem
        segment = search_writer.append(path.read_bytes())
        search_segments[prefix] = segment.as_json()
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
            "bundles": bundle_metadata(
                bulk_index_root, search_bundles, base_url
            ),
            "segments": search_segments,
        },
        "records": {
            "page_size": int(record_manifest["page_size"]),
            "page_count": len(record_segments),
            "fields": record_manifest.get("fields", []),
            "bundles": bundle_metadata(
                bulk_index_root, record_bundles, base_url
            ),
            "pages": record_segments,
        },
    }
    write_json(site / "search-index.json", config)

    for manifest_path in site.glob("*/downloads/dataset-manifest.json"):
        manifest = load_json(manifest_path)
        manifest["search"] = {
            "mode": "release-range-index-v1",
            "minimum_query_characters": config["minimum_query_characters"],
            "manifest": "../../search-index.json",
        }
        write_json(manifest_path, manifest)

    for html_path in site.glob("*/documents.html"):
        markup = html_path.read_text(encoding="utf-8")
        markup = markup.replace(
            "Search uses compact canonical metadata shards, never raw corpus payloads.",
            "Search loads only byte ranges from immutable canonical metadata bundles, never raw corpus payloads.",
        )
        html_path.write_text(markup, encoding="utf-8")

    root_search = site / "search.html"
    if root_search.is_file():
        markup = root_search.read_text(encoding="utf-8")
        markup = markup.replace(
            "The browser loads one compact token-prefix shard and only the canonical metadata pages needed for matching records.",
            "The browser loads only the byte ranges needed from immutable search and canonical metadata bundles.",
        )
        root_search.write_text(markup, encoding="utf-8")

    shutil.rmtree(indexes)
    return config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move generated static search indexes out of GitHub Pages into range-addressable bundles"
    )
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--bulk", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--bundle-limit", type=int, default=DEFAULT_BUNDLE_LIMIT
    )
    args = parser.parse_args()
    config = externalize(args.site, args.bulk, args.base_url, args.bundle_limit)
    search_bundle_count = len(config["search"]["bundles"])
    record_bundle_count = len(config["records"]["bundles"])
    print(
        f"external_index_records={config['record_count']} "
        f"record_bundles={record_bundle_count} "
        f"search_bundles={search_bundle_count} "
        f"search_segments={len(config['search']['segments'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
