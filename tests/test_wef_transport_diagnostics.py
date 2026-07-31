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


def probe(encoded: str, position: int) -> int:
    candidate = encoded[:position] + "A" + encoded[position:]
    compressed = base64.b64decode(candidate, validate=True)
    return first_xz_error_byte(compressed)


class WefTransportDiagnostics(unittest.TestCase):
    def test_transport_failure_plateau(self) -> None:
        directory = ROOT / "imports" / ".wef-shapers-compact"
        encoded = "".join(
            "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
            for path in sorted(directory.glob("part-*"))
        )
        positions = [120_000, 135_000, 140_000, 145_000, 148_000, 150_000, 151_000, 152_000, 153_000, 155_000, 160_000, 180_000, encoded.find("=")]
        results = [(position, probe(encoded, position)) for position in positions]
        self.fail(f"WEF_TRANSPORT_PLATEAU {results}")


if __name__ == "__main__":
    unittest.main()
