from __future__ import annotations

import base64
import hashlib
import json
import lzma
import string
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE64_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"
PLATEAU_ERROR_BYTE = 113_999


def first_xz_error_byte(compressed: bytes) -> int:
    decoder = lzma.LZMADecompressor()
    for index, byte in enumerate(compressed):
        try:
            decoder.decompress(bytes((byte,)))
        except lzma.LZMAError:
            return index
    return len(compressed)


def decode_with_insert(encoded: str, position: int, character: str) -> bytes:
    candidate = encoded[:position] + character + encoded[position:]
    return base64.b64decode(candidate, validate=True)


def probe(encoded: str, position: int) -> int:
    return first_xz_error_byte(decode_with_insert(encoded, position, "A"))


def first_plateau(encoded: str, start: int, stop: int, step: int) -> int:
    positions = range(start, stop + 1, step)
    matches = [position for position in positions if probe(encoded, position) == PLATEAU_ERROR_BYTE]
    if not matches:
        raise AssertionError(f"No XZ failure plateau in {start}:{stop}:{step}")
    return min(matches)


class WefTransportDiagnostics(unittest.TestCase):
    def test_recover_transport_character(self) -> None:
        directory = ROOT / "imports" / ".wef-shapers-compact"
        encoded = "".join(
            "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
            for path in sorted(directory.glob("part-*"))
        )

        coarse = first_plateau(encoded, 151_000, 152_000, 100)
        fine = first_plateau(encoded, max(151_000, coarse - 100), coarse, 10)
        exact = first_plateau(encoded, max(151_000, fine - 10), fine, 1)

        recovered: tuple[int, str, bytes] | None = None
        for position in range(max(0, exact - 8), min(len(encoded), exact + 8) + 1):
            for character in BASE64_ALPHABET:
                try:
                    payload = lzma.decompress(decode_with_insert(encoded, position, character))
                except (ValueError, lzma.LZMAError):
                    continue
                recovered = (position, character, payload)
                break
            if recovered is not None:
                break

        self.assertIsNotNone(recovered, f"No valid repair around plateau position {exact}")
        assert recovered is not None
        position, character, payload = recovered
        documents = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line.strip()]
        canonical = "".join(
            json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for document in documents
        )
        digest = hashlib.sha256(canonical.encode()).hexdigest()

        print(
            f"WEF_TRANSPORT_RECOVERED position={position} character={character!r} "
            f"records={len(documents)} sha256={digest}"
        )
        self.assertEqual(len(documents), 12_187)
        self.assertEqual(
            digest,
            "82408fb3baa6d2fcbba1948801a26827ccdbf6e5b2a18685502a7ca70b2f070f",
        )


if __name__ == "__main__":
    unittest.main()
