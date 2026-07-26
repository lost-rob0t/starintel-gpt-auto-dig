#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
from pathlib import Path

root = Path(__file__).resolve().parent
payload = "".join(
    (root / f".tmp-flock-cpd-control-plane.b64.{index:02d}").read_text(encoding="utf-8").strip()
    for index in range(4)
)
source = gzip.decompress(base64.b64decode(payload))
virtual_path = root / "generate-flock-cpd-control-plane.py"
namespace = {"__name__": "__main__", "__file__": str(virtual_path)}
exec(compile(source, str(virtual_path), "exec"), namespace)
