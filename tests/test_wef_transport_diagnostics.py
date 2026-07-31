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
        boundaries: list[int] = []
        offset = 0
        for value in values[:-1]:
            offset += len(value)
            boundaries.append(offset)
        padding_at = encoded.find("=")
        if padding_at >= 0:
            boundaries.append(padding_at)

        print(
            f"DIAG compact parts={len(parts)} lengths={lengths} total={len(encoded)} "
            f"mod4={len(encoded) % 4} boundaries={boundaries} "
            f"prefix={encoded[:24]!r} suffix={encoded[-24:]!r}"
        )

        recovered: tuple[int, str, bytes] | None = None
        for position in boundaries:
            for character in BASE64_ALPHABET:
                candidate = encoded[:position] + character + encoded[position:]
                try:
                    compressed = base64.b64decode(candidate, validate=True)
                    payload = lzma.decompress(compressed)
                except Exception:
                    continue
                recovered = (position, character, payload)
                break
            if recovered is not None:
                break

        self.assertIsNotNone(recovered, "No single-character repair succeeded at a chunk boundary")
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
