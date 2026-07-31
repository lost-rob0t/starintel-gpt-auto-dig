from __future__ import annotations

import base64
import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path

from starintel_doc.store import read_transport


class TransportRecoveryTests(unittest.TestCase):
    def test_crc_failure_recovers_only_with_matching_sha256(self) -> None:
        payload = b'{"_id":"example"}\n'
        encoded = bytearray(gzip.compress(payload, mtime=0))
        encoded[-8] ^= 0x01

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "starintel-documents.jsonl.gz.b64"
            path.write_bytes(base64.b64encode(encoded))

            with self.assertRaises(gzip.BadGzipFile):
                read_transport(path)

            digest = hashlib.sha256(payload).hexdigest()
            (root / "starintel-documents.jsonl.sha256").write_text(
                f"{digest}  starintel-documents.jsonl\n",
                encoding="utf-8",
            )
            self.assertEqual(read_transport(path), payload.decode("utf-8"))

    def test_crc_recovery_rejects_wrong_sha256(self) -> None:
        payload = b'{"_id":"example"}\n'
        encoded = bytearray(gzip.compress(payload, mtime=0))
        encoded[-8] ^= 0x01

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "starintel-documents.jsonl.gz.b64"
            path.write_bytes(base64.b64encode(encoded))
            (root / "starintel-documents.jsonl.sha256").write_text(
                f"{'0' * 64}  starintel-documents.jsonl\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "CRC recovery rejected"):
                read_transport(path)


if __name__ == "__main__":
    unittest.main()
