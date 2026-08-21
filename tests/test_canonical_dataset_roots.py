import unittest
from pathlib import Path


class CanonicalDatasetRootTests(unittest.TestCase):
    def test_flock_uses_single_canonical_dataset_root(self) -> None:
        digs = Path("digs")
        canonical = digs / "flock"
        aliases = sorted(
            path.name
            for path in digs.iterdir()
            if path.is_dir() and path.name.startswith("flock-")
        )

        self.assertTrue(canonical.is_dir(), "Flock research must live under digs/flock/")
        self.assertEqual(
            aliases,
            [],
            "Flock research must not create sibling dataset roots; move these under "
            f"digs/flock/: {', '.join(aliases)}",
        )


if __name__ == "__main__":
    unittest.main()
