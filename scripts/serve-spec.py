#!/usr/bin/env python3
"""Serve the StarIntel spec bundles over HTTP for every downstream language.

Routes (all versioned artifacts are immutable content; cache them forever):

  GET /                          release index (JSON)
  GET /releases                  same as /
  GET /release/<version>         manifest JSON for a release
  GET /schema/<version>          generated JSON Schema
  GET /schema/starintel-doc-<version>.schema.json   canonical $id shape
  GET /manifest/<version>        manifest JSON
  GET /star/<version>            Star-Lang spec-library export (text)
  GET /sha256/<version>          SHA256SUMS for the release bundle
  GET /lock/<version>            consumer-style lock JSON (pins everything)

The server is deliberately stdlib-only so it runs anywhere: bare metal,
containers, or a NixOS systemd unit (see the starintel-infra module). It
serves a checkout of the canonical schema repository; deployments must pin
that checkout to a reviewed commit.

Usage:
  python3 scripts/serve-spec.py --root /path/to/starintel-gpt-auto-dig \
      --base https://spec.starintel.actor --bind 127.0.0.1 --port 8787
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

IMMUTABLE = {"Cache-Control": "public, max-age=31536000, immutable"}
JSON_TYPE = {"Content-Type": "application/json; charset=utf-8"}
STAR_TYPE = {"Content-Type": "text/plain; charset=utf-8"}
SOLIDUS_TYPE = {"Content-Type": "text/plain; charset=utf-8"}

ROOT = Path(".")


def git_head(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
            text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_releases(root: Path) -> dict[str, dict[str, object]]:
    """Index every manifest under schemas/ into {version: artifact map}."""
    releases: dict[str, dict[str, object]] = {}
    for manifest_path in sorted((root / "schemas").glob("*.manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        release = manifest.get("release_version")
        if not release:
            continue
        base_schema = manifest.get("base_schema_path")
        schema_file = root / base_schema if base_schema else manifest_path
        star_file = root / "spec" / "star" / f"starintel-core-{release}.star"
        entry: dict[str, object] = {
            "release_version": release,
            "schema_version": manifest.get("schema_version"),
            "profile": manifest.get("profile"),
            "schema_revision": manifest.get("schema_revision"),
            "manifest_path": str(manifest_path.relative_to(root)),
            "schema_path": str(schema_file.relative_to(root))
            if schema_file.exists() else None,
            "star_path": str(star_file.relative_to(root))
            if star_file.exists() else None,
        }
        if schema_file.exists():
            entry["schema_sha256"] = sha256_file(schema_file)
        if star_file.exists():
            entry["star_sha256"] = sha256_file(star_file)
        releases[release] = entry
    return releases


class SpecRegistry:
    def __init__(self, root: Path, base: str) -> None:
        self.root = root
        self.base = base.rstrip("/")
        self.releases = discover_releases(root)
        self.commit = git_head(root)

    def lock_for(self, version: str) -> dict[str, object] | None:
        entry = self.releases.get(version)
        if entry is None:
            return None
        star_sha = entry.get("star_sha256")
        return {
            "release_version": entry["release_version"],
            "schema_version": entry["schema_version"],
            "profile": entry["profile"],
            "schema_revision": entry["schema_revision"],
            "canonical_repository": "lost-rob0t/starintel-gpt-auto-dig",
            "canonical_commit": self.commit,
            "schema_path": entry["schema_path"],
            "manifest_path": entry["manifest_path"],
            "star_path": entry.get("star_path"),
            "schema_sha256": entry.get("schema_sha256"),
            "star_sha256": star_sha,
            "star_import_digest": f"sha256:{star_sha}" if star_sha else None,
            "http": {
                "index": f"{self.base}/releases",
                "schema": f"{self.base}/schema/{version}",
                "manifest": f"{self.base}/manifest/{version}",
                "star": f"{self.base}/star/{version}",
                "lock": f"{self.base}/lock/{version}",
            },
        }

    def sums_for(self, version: str) -> str:
        entry = self.releases.get(version)
        if entry is None:
            return ""
        lines = []
        for key, name in (("schema_sha256", entry["schema_path"]),
                          ("star_sha256", entry.get("star_path"))):
            digest = entry.get(key)
            if digest and name:
                lines.append(f"{digest}  {Path(name).name}")
        manifest_name = Path(str(entry["manifest_path"])).name
        manifest_file = self.root / str(entry["manifest_path"])
        lines.append(f"{sha256_file(manifest_file)}  {manifest_name}")
        return "\n".join(sorted(lines)) + "\n"


class SpecHandler(BaseHTTPRequestHandler):
    registry: SpecRegistry

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/")
        if not path:
            path = "/"
        routes = {
            "/": self._index,
            "/releases": self._index,
        }
        if path in routes:
            routes[path]()
            return
        parts = path.lstrip("/").split("/")
        if len(parts) == 2:
            kind, value = parts
            if kind == "schema" and value.endswith(".json"):
                self._schema_file(value)
                return
            handlers = {
                "schema": self._schema,
                "manifest": self._manifest,
                "release": self._manifest,
                "star": self._star,
                "sha256": self._sha256,
                "lock": self._lock,
            }
            if kind in handlers:
                handlers[kind](value)
                return
        self._send_json({"error": "not found", "path": path}, 404)

    def _send_bytes(self, body: bytes, status: int, headers: dict[str, str]) -> None:
        self.send_response(status)
        for key, value in {**headers, "Content-Length": str(len(body))}.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200,
                   immutable: bool = False) -> None:
        headers = dict(JSON_TYPE)
        if immutable:
            headers.update(IMMUTABLE)
        self._send_bytes(
            json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n",
            status, headers)

    def _send_text(self, text: str, status: int = 200,
                   content_type: dict[str, str] | None = None,
                   immutable: bool = False) -> None:
        headers = dict(content_type or STAR_TYPE)
        if immutable:
            headers.update(IMMUTABLE)
        self._send_bytes(text.encode("utf-8"), status, headers)

    def _index(self) -> None:
        self._send_json({
            "service": "starintel-spec-registry",
            "canonical_repository":
                self.registry.releases and
                "lost-rob0t/starintel-gpt-auto-dig",
            "served_commit": self.registry.commit,
            "releases": {
                version: f"{self.registry.base}/lock/{version}"
                for version in sorted(self.registry.releases)
            },
        })

    def _entry_or_404(self, version: str) -> dict | None:
        entry = self.registry.releases.get(version)
        if entry is None:
            self._send_json({"error": "unknown release", "version": version},
                            404)
        return entry

    def _schema(self, version: str) -> None:
        entry = self._entry_or_404(version)
        if entry:
            self._send_file(self.registry.root / str(entry["schema_path"]),
                            JSON_TYPE)

    def _schema_file(self, filename: str) -> None:
        self._send_file(self.registry.root / "schemas" / filename, JSON_TYPE)

    def _manifest(self, version: str) -> None:
        entry = self._entry_or_404(version)
        if entry:
            self._send_file(self.registry.root / str(entry["manifest_path"]),
                            JSON_TYPE)

    def _star(self, version: str) -> None:
        entry = self._entry_or_404(version)
        if entry and entry.get("star_path"):
            self._send_file(self.registry.root / str(entry["star_path"]),
                            STAR_TYPE)
        elif entry:
            self._send_json({"error": "no star-lang export", "version": version},
                            404)

    def _sha256(self, version: str) -> None:
        if self._entry_or_404(version):
            self._send_text(self.registry.sums_for(version),
                            content_type=SOLIDUS_TYPE)

    def _lock(self, version: str) -> None:
        lock = self.registry.lock_for(version)
        if lock is None:
            self._send_json({"error": "unknown release", "version": version},
                            404)
        else:
            self._send_json(lock, immutable=True)

    def _send_file(self, path: Path, content_type: dict[str, str]) -> None:
        if not path.is_file():
            self._send_json({"error": "not found", "path": str(path)}, 404)
            return
        body = path.read_bytes()
        self._send_bytes(body, 200, {**content_type, **IMMUTABLE})

    def log_message(self, fmt: str, *args) -> None:  # silence stdlib noise
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="canonical starintel-gpt-auto-dig checkout to serve")
    parser.add_argument("--base", default="http://127.0.0.1:8787",
                        help="external base URL recorded in locks")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    registry = SpecRegistry(args.root, args.base)
    if not registry.releases:
        print("no manifests found under schemas/; wrong --root?", file=sys.stderr)
        return 1

    handler = type("BoundSpecHandler", (SpecHandler,), {"registry": registry})
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"serving {len(registry.releases)} releases from {args.root}"
          f" at {args.bind}:{args.port} (base {args.base})", file=sys.stderr)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
