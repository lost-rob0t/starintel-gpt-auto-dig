from __future__ import annotations

import base64
import lzma
import string
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE64_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"
FIRST_INSERT_POSITION = 151_980
FIRST_INSERT_CHARACTER = "1"


def repaired_encoded() -> str:
    directory = ROOT / "imports" / ".wef-shapers-compact"
    encoded = "".join(
        "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
        for path in sorted(directory.glob("part-*"))
    )
    return encoded[:FIRST_INSERT_POSITION] + FIRST_INSERT_CHARACTER + encoded[FIRST_INSERT_POSITION:]


def xz_progress(compressed: bytes, chunk_size: int = 1024) -> int:
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
    def test_rank_second_transport_repairs(self) -> None:
        encoded = repaired_encoded()
        candidates: list[tuple[int, int, str, str]] = []
        for position in range(160_430, 160_511):
            original = encoded[position]
            for character in BASE64_ALPHABET:
                if character == original:
                    continue
                candidate = encoded[:position] + character + encoded[position + 1 :]
                compressed = base64.b64decode(candidate, validate=True)
                candidates.append((xz_progress(compressed), position, original, character))
        candidates.sort(reverse=True)
        self.fail(f"WEF_TRANSPORT_SECOND_REPAIR_CANDIDATES {candidates[:20]}")


if __name__ == "__main__":
    unittest.main()
