#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "imports" / "global-shapers" / "import_global_shapers_people.py.gz.b64"
GENERATED = ROOT / ".generated" / "import_global_shapers_people.py"
HUB_URL_FILE = ROOT / "imports" / "global-shapers" / "generated-hub-urls.txt"
PROFILE_URL_FILE = ROOT / "imports" / "global-shapers" / "generated-member-profile-urls.txt"
SOURCE_SHA256 = "1b75a51d5b55fe830744bae144d26cb8bd14d0fe0a026f3797a03be453c4068f"
GZIP_SHA256 = "2bed654326ccea87c53908ba40998808cf0ce04007f76fca2a56b1c5919ae249"


def restore() -> Path:
    encoded = "".join(PAYLOAD.read_text(encoding="utf-8").split())
    compressed = base64.b64decode(encoded, validate=True)
    actual_gzip = hashlib.sha256(compressed).hexdigest()
    if actual_gzip != GZIP_SHA256:
        raise RuntimeError(f"compressed importer digest mismatch: {actual_gzip}")
    source = gzip.decompress(compressed)
    actual_source = hashlib.sha256(source).hexdigest()
    if actual_source != SOURCE_SHA256:
        raise RuntimeError(f"importer source digest mismatch: {actual_source}")
    GENERATED.parent.mkdir(parents=True, exist_ok=True)
    GENERATED.write_bytes(source)
    return GENERATED


def supported_seed_arguments(importer: Path) -> list[str]:
    help_run = subprocess.run(
        [sys.executable, str(importer), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    help_text = help_run.stdout + help_run.stderr
    extra: list[str] = []
    if HUB_URL_FILE.is_file() and "--hub-url-file" in help_text:
        extra.extend(["--hub-url-file", str(HUB_URL_FILE)])
    if PROFILE_URL_FILE.is_file() and "--profile-url-file" in help_text:
        extra.extend(["--profile-url-file", str(PROFILE_URL_FILE)])
    return extra


def main() -> int:
    importer = restore()
    subprocess.run([sys.executable, "-m", "py_compile", str(importer)], check=True)
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        return subprocess.run([sys.executable, str(importer), *sys.argv[1:]], cwd=ROOT).returncode

    env = os.environ.copy()
    env["GLOBAL_SHAPERS_HUB_URL_FILE"] = str(HUB_URL_FILE)
    env["GLOBAL_SHAPERS_PROFILE_URL_FILE"] = str(PROFILE_URL_FILE)
    extra = supported_seed_arguments(importer)
    completed = subprocess.run(
        [sys.executable, str(importer), *sys.argv[1:], *extra],
        cwd=ROOT,
        env=env,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
