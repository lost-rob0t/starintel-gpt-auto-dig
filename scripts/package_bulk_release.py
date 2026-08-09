from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gzip_file(source: Path, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_stream, destination.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=6, mtime=0, fileobj=raw_output) as output_stream:
            for chunk in iter(lambda: input_stream.read(1024 * 1024), b""):
                output_stream.write(chunk)
    return {
        "asset": destination.name,
        "compressed_size_bytes": destination.stat().st_size,
        "compressed_sha256": sha256(destination),
        "raw_size_bytes": source.stat().st_size,
        "raw_sha256": sha256(source),
    }


def package_bulk(bulk: Path, site: Path, output: Path, base_url: str) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = site / "downloads" / "starintel-complete-corpus.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest["data"]["files"]
    release_assets: list[dict[str, Any]] = []

    for item in files:
        asset_name = str(item["path"])
        if not asset_name.endswith(".jsonl.gz"):
            raise ValueError(f"unexpected corpus asset name: {asset_name}")
        raw_name = asset_name.removesuffix(".gz")
        source = bulk / "corpus" / raw_name
        if not source.is_file():
            raise FileNotFoundError(source)
        packaged = gzip_file(source, output / asset_name)
        if packaged["raw_sha256"] != item["raw_sha256"]:
            raise ValueError(f"raw corpus shard hash changed: {raw_name}")
        if packaged["raw_size_bytes"] != int(item["raw_size_bytes"]):
            raise ValueError(f"raw corpus shard size changed: {raw_name}")
        item["compressed_size_bytes"] = packaged["compressed_size_bytes"]
        item["compressed_sha256"] = packaged["compressed_sha256"]
        item["url"] = f"{base_url.rstrip('/')}/{asset_name}"
        release_assets.append({"kind": "corpus-shard", **packaged, "url": item["url"]})

    membership_root = bulk / "memberships"
    membership_assets: list[dict[str, Any]] = []
    if membership_root.is_dir():
        for source in sorted(membership_root.glob("*.ids")):
            asset_name = f"{source.name}.gz"
            packaged = gzip_file(source, output / asset_name)
            packaged.update(
                {
                    "kind": "dataset-membership",
                    "url": f"{base_url.rstrip('/')}/{asset_name}",
                }
            )
            membership_assets.append(packaged)
            release_assets.append(packaged)

    release_manifest = {
        "format": "starintel-auto-dig-bulk-release-v1",
        "base_url": base_url.rstrip("/"),
        "canonical_record_count": int(manifest["data"]["record_count"]),
        "canonical_sha256": str(manifest["data"]["content_hash"]),
        "canonical_size_bytes": int(manifest["data"]["canonical_size_bytes"]),
        "corpus_shards": files,
        "memberships": membership_assets,
        "asset_count": len(release_assets),
    }
    release_manifest_path = output / "starintel-bulk-release.manifest.json"
    release_manifest_path.write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    release_assets.append(
        {
            "kind": "release-manifest",
            "asset": release_manifest_path.name,
            "compressed_size_bytes": release_manifest_path.stat().st_size,
            "compressed_sha256": sha256(release_manifest_path),
            "url": f"{base_url.rstrip('/')}/{release_manifest_path.name}",
        }
    )

    manifest["data"]["distribution_manifest"] = f"{base_url.rstrip('/')}/{release_manifest_path.name}"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (site / "downloads" / "starintel-bulk-release.manifest.json").write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return release_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Package StarIntel bulk shards for a GitHub Release")
    parser.add_argument("--bulk", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    release_manifest = package_bulk(args.bulk, args.site, args.output, args.base_url)
    print(
        "bulk_release_assets="
        f"{release_manifest['asset_count']} "
        f"records={release_manifest['canonical_record_count']} "
        f"canonical_bytes={release_manifest['canonical_size_bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
