from __future__ import annotations

import base64
import lzma
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST_REPAIR_CANDIDATES = (
    (151_980, "1"),
    (151_970, "9"),
    (151_926, "/"),
    (151_902, "d"),
)


def decode_with_insert(encoded: str, position: int, character: str) -> bytes:
    candidate = encoded[:position] + character + encoded[position:]
    return base64.b64decode(candidate, validate=True)


def exact_xz_progress(compressed: bytes) -> tuple[int, int]:
    decoder = lzma.LZMADecompressor()
    output_bytes = 0
    for index, byte in enumerate(compressed):
        try:
            output_bytes += len(decoder.decompress(bytes((byte,))))
        except lzma.LZMAError:
            return index, output_bytes
        if decoder.eof:
            return len(compressed), output_bytes
    return len(compressed), output_bytes


class WefTransportDiagnostics(unittest.TestCase):
    def test_rank_first_transport_repairs_exactly(self) -> None:
        directory = ROOT / "imports" / ".wef-shapers-compact"
        encoded = "".join(
            "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
            for path in sorted(directory.glob("part-*"))
        )
        results = []
        for position, character in FIRST_REPAIR_CANDIDATES:
            compressed = decode_with_insert(encoded, position, character)
            input_progress, output_bytes = exact_xz_progress(compressed)
            results.append((input_progress, output_bytes, position, character))
        results.sort(reverse=True)
        self.fail(f"WEF_TRANSPORT_FIRST_REPAIR_EXACT {results}")


if __name__ == "__main__":
    unittest.main()
