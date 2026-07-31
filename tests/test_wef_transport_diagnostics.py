from __future__ import annotations

import base64
import lzma
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def first_xz_error_byte(compressed: bytes) -> int:
    decoder = lzma.LZMADecompressor()
    for index, byte in enumerate(compressed):
        try:
            decoder.decompress(bytes((byte,)))
        except lzma.LZMAError:
            return index
    return len(compressed)


class WefTransportDiagnostics(unittest.TestCase):
    def test_transport_failure_offset(self) -> None:
        directory = ROOT / "imports" / ".wef-shapers-compact"
        encoded = "".join(
            "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
            for path in sorted(directory.glob("part-*"))
        )
        padding_at = encoded.find("=")
        self.assertGreaterEqual(padding_at, 0)
        candidate = encoded[:padding_at] + "A" + encoded[padding_at:]
        compressed = base64.b64decode(candidate, validate=True)
        error_byte = first_xz_error_byte(compressed)
        estimate = (error_byte * 4) // 3
        self.fail(
            f"WEF_TRANSPORT_OFFSET encoded={len(encoded)} padding_at={padding_at} "
            f"compressed={len(compressed)} error_byte={error_byte} estimate={estimate}"
        )


if __name__ == "__main__":
    unittest.main()
