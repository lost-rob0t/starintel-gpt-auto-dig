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


def decode_with_insert(encoded: str, position: int, character: str) -> bytes:
    candidate = encoded[:position] + character + encoded[position:]
    return base64.b64decode(candidate, validate=True)


def first_xz_error_byte(compressed: bytes) -> int:
    decoder = lzma.LZMADecompressor()
    for index, byte in enumerate(compressed):
        try:
            decoder.decompress(bytes((byte,)))
        except lzma.LZMAError:
            return index
    return len(compressed)


class WefTransportDiagnostics(unittest.TestCase):
    def test_transport_framing(self) -> None:
        compact_dir = ROOT / "imports" / ".wef-shapers-compact"
        parts = sorted(compact_dir.glob("part-*"))
        values = [
            "".join(path.read_text(encoding="utf-8").lstrip("\ufeff").split())
            for path in parts
        ]
        encoded = "".join(values)
        lengths = [len(value) for value in values]
        padding_at = encoded.find("=")
        self.assertGreaterEqual(padding_at, 0)

        probe = decode_with_insert(encoded, padding_at, "A")
        error_byte = first_xz_error_byte(probe)
        estimate = max(0, min(padding_at, (error_byte * 4) // 3))
        positions = range(max(0, estimate - 1024), min(padding_at, estimate + 1024) + 1)

        print(
            f"DIAG compact parts={len(parts)} lengths={lengths} total={len(encoded)} "
            f"padding_at={padding_at} probe_bytes={len(probe)} error_byte={error_byte} "
            f"estimate={estimate} search={positions.start}:{positions.stop}"
        )

        recovered: tuple[int, str, bytes] | None = None
        for position in positions:
            for character in BASE64_ALPHABET:
                try:
                    compressed = decode_with_insert(encoded, position, character)
                    payload = lzma.decompress(compressed)
                except Exception:
                    continue
                recovered = (position, character, payload)
                break
            if recovered is not None:
                break

        self.assertIsNotNone(recovered, "No single-character repair succeeded near the XZ failure offset")
        assert recovered is not None
        position, character, payload = recovered
        lines = [line for line in payload.decode("utf-8").splitlines() if line.strip()]
        documents = [json.loads(line) for line in lines]
        canonical = "".join(
            json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for document in documents
        )
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        print(
            f"RECOVER position={position} character={character!r} payload={len(payload)} "
            f"records={len(documents)} sha256={digest}"
        )
        self.assertEqual(len(documents), 12_187)
        self.assertEqual(
            digest,
            "82408fb3baa6d2fcbba1948801a26827ccdbf6e5b2a18685502a7ca70b2f070f",
        )


if __name__ == "__main__":
    unittest.main()
