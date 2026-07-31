from __future__ import annotations

import base64
import lzma
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WefTransportDiagnostics(unittest.TestCase):
    def test_transport_framing(self) -> None:
        failures: list[str] = []
        for relative in (
            "imports/.wef-shapers-compact",
            "imports/.wef-shapers-source",
        ):
            directory = ROOT / relative
            parts = sorted(directory.glob("part-*"))
            encoded = "".join(
                "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
                for path in parts
            )
            padded = encoded + "=" * (-len(encoded) % 4)
            print(
                f"DIAG {relative} parts={len(parts)} encoded={len(encoded)} "
                f"mod4={len(encoded) % 4} prefix={encoded[:24]!r} suffix={encoded[-24:]!r}"
            )
            try:
                compressed = base64.b64decode(padded, validate=False)
            except Exception as exc:
                failures.append(f"{relative}: base64 {type(exc).__name__}: {exc}")
                continue
            print(
                f"DIAG {relative} decoded={len(compressed)} "
                f"prefix_hex={compressed[:24].hex()} xz_magic={compressed.find(bytes.fromhex('fd377a585a00'))}"
            )
            try:
                payload = lzma.decompress(compressed)
            except Exception as exc:
                failures.append(f"{relative}: xz {type(exc).__name__}: {exc}")
                continue
            print(
                f"DIAG {relative} payload={len(payload)} "
                f"payload_prefix={payload[:80]!r}"
            )
        self.assertFalse(failures, " | ".join(failures))


if __name__ == "__main__":
    unittest.main()
