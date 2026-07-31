from __future__ import annotations

import base64
import lzma
import string
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE64_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"


def decode_with_insert(encoded: str, position: int, character: str) -> bytes:
    candidate = encoded[:position] + character + encoded[position:]
    return base64.b64decode(candidate, validate=True)


def xz_progress(compressed: bytes, chunk_size: int = 2048) -> int:
    decoder = lzma.LZMADecompressor()
    offset = 0
    while offset < len(compressed):
        chunk = compressed[offset : offset + chunk_size]
        try:
            decoder.decompress(chunk)
        except lzma.LZMAError:
            return offset
        offset += len(chunk)
        if decoder.eof:
            return len(compressed)
    return offset


class WefTransportDiagnostics(unittest.TestCase):
    def test_find_first_transport_repair(self) -> None:
        directory = ROOT / "imports" / ".wef-shapers-compact"
        encoded = "".join(
            "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
            for path in sorted(directory.glob("part-*"))
        )

        candidates: list[tuple[int, int, str]] = []
        for position in range(151_900, 152_101):
            for character in BASE64_ALPHABET:
                try:
                    progress = xz_progress(decode_with_insert(encoded, position, character))
                except ValueError:
                    continue
                candidates.append((progress, position, character))

        candidates.sort(reverse=True)
        self.fail(f"WEF_TRANSPORT_REPAIR_CANDIDATES {candidates[:20]}")


if __name__ == "__main__":
    unittest.main()
