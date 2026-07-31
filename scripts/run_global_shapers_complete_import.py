#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "imports" / "global-shapers" / "import_global_shapers_people.py.gz.b64"
GENERATED = ROOT / ".generated" / "import_global_shapers_people.py"
SOURCE_SHA256 = "1b75a51d5b55fe830744bae144d26cb8bd14d0fe0a026f3797a03be453c4068f"
GZIP_SHA256 = "d1bdbf26070763cc45807bd2b2bcc21693a7de7c36b7198604f08c7ceb8041f9"


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


def main() -> int:
    importer = restore()
    subprocess.run([sys.executable, "-m", "py_compile", str(importer)], check=True)
    completed = subprocess.run([sys.executable, str(importer), *sys.argv[1:]], cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
