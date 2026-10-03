"""Consume the maintained Python runtime; StarLang owns every schema field."""
import hashlib
import json
from pathlib import Path

from starintel_canonical import *  # noqa: F403
from starintel_canonical import RELEASE_ROOT

ROOT = Path(__file__).resolve().parents[1]

def verify_runtime_release() -> None:
    lock = json.loads((ROOT / "schema/starintel-schema.lock.json").read_text())
    for path, entry in lock["vendored_files"].items():
        relative = entry["source"].split("/0.10.1/", 1)[1]
        installed = RELEASE_ROOT / relative
        if hashlib.sha256(installed.read_bytes()).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"installed StarIntel runtime differs from StarLang release: {relative}")
    runtime_lock = json.loads((ROOT / "schema/starintel-runtime.lock.json").read_text())
    dependency = f"starintel-doc @ git+https://github.com/{runtime_lock['python_repository']}.git@{runtime_lock['python_commit']}"
    if dependency not in (ROOT / "pyproject.toml").read_text():
        raise RuntimeError("Python runtime dependency differs from its immutable lock")
    # CI checks out the exact maintained Nim runtime. Its own complete source
    # mapping must agree, rather than merely exposing the same version label.
    nim_root = ROOT / ".starintel-doc-nim"
    if not nim_root.is_dir():
        raise RuntimeError("missing pinned Nim runtime checkout")
    nim_lock = json.loads((nim_root / "schema/starintel-schema.lock.json").read_text())
    if {k: v for k, v in lock.items() if k != "vendored_files"} != {k: v for k, v in nim_lock.items() if k != "vendored_files"}:
        raise RuntimeError("Nim and Python consumers disagree about StarLang authority")
    for path, entry in nim_lock["vendored_files"].items():
        if hashlib.sha256((nim_root / path).read_bytes()).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"Nim runtime release file differs: {path}")
    nim_sources = {entry["source"]: entry["sha256"] for entry in nim_lock["vendored_files"].values()}
    if nim_sources != {entry["source"]: entry["sha256"] for entry in lock["vendored_files"].values()}:
        raise RuntimeError("Nim runtime generated release differs from this consumer")
    import subprocess
    nim_head = subprocess.check_output(["git", "-C", str(nim_root), "rev-parse", "HEAD"], text=True).strip()
    if nim_head != runtime_lock["nim_commit"]:
        raise RuntimeError("Nim checkout differs from its immutable runtime commit")
    import tomllib
    config = tomllib.loads((ROOT / "starintel-runtime.toml").read_text())
    if config["nim_commit"] != runtime_lock["nim_commit"]:
        raise RuntimeError("Nim runtime dependency differs from its immutable lock")

