from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "extract_iphone_backup.py"
SPEC = importlib.util.spec_from_file_location("extract_iphone_backup", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExtractIphoneBackupTests(unittest.TestCase):
    def test_sha256_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            path.write_bytes(b"starintel")
            expected = hashlib.sha256(b"starintel").hexdigest()
            self.assertEqual(MODULE.sha256_file(path), expected)

    def test_resolve_passphrase_prefers_cli_value(self) -> None:
        args = argparse.Namespace(password="secret", password_env=None)
        self.assertEqual(MODULE.resolve_passphrase(args), "secret")

    def test_resolve_passphrase_reads_environment(self) -> None:
        args = argparse.Namespace(password=None, password_env="IPHONE_BACKUP_PASSWORD")
        with mock.patch.dict(os.environ, {"IPHONE_BACKUP_PASSWORD": "secret"}, clear=False):
            self.assertEqual(MODULE.resolve_passphrase(args), "secret")

    def test_resolve_passphrase_rejects_missing_environment_variable(self) -> None:
        args = argparse.Namespace(password=None, password_env="MISSING_BACKUP_PASSWORD")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "is not set"):
                MODULE.resolve_passphrase(args)

    def test_validate_backup_directory_requires_manifest_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with self.assertRaisesRegex(ValueError, "Manifest.db"):
                MODULE.validate_backup_directory(path)

    def test_parse_defaults_to_complete_domain_preserving_export(self) -> None:
        args = MODULE.parse_args(["--directory", "/backup", "--output", "/output"])
        self.assertEqual(args.relative_path_like, "%")
        self.assertEqual(args.domain_like, "%")
        self.assertFalse(args.manifest_only)
        self.assertFalse(args.skip_call_history)
        self.assertFalse(args.incremental)


if __name__ == "__main__":
    unittest.main()
