import json
import re
import unittest
from pathlib import Path


ROOT_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CanonicalDatasetRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.digs = Path("digs")
        self.roots = sorted(
            path.name
            for path in self.digs.iterdir()
            if path.is_dir()
        )
        self.root_set = set(self.roots)

    def test_dataset_roots_use_canonical_kebab_case(self) -> None:
        invalid = [root for root in self.roots if ROOT_NAME.fullmatch(root) is None]
        self.assertEqual(
            invalid,
            [],
            f"dataset roots must use lowercase kebab-case: {', '.join(invalid)}",
        )

    def test_no_dataset_root_has_hyphen_qualified_sibling(self) -> None:
        siblings = sorted(
            (canonical, candidate)
            for canonical in self.roots
            for candidate in self.roots
            if canonical != candidate and candidate.startswith(f"{canonical}-")
        )
        self.assertEqual(
            siblings,
            [],
            "dataset siblings are forbidden; move packets into the canonical root: "
            + ", ".join(f"{candidate} -> {canonical}" for canonical, candidate in siblings),
        )

    def test_retired_dataset_root_aliases_cannot_reappear(self) -> None:
        aliases = json.loads(Path("config/dataset-root-aliases.json").read_text(encoding="utf-8"))
        missing_canonical = sorted(
            canonical
            for canonical in set(aliases.values())
            if canonical not in self.root_set
        )
        resurrected = sorted(alias for alias in aliases if alias in self.root_set)

        self.assertEqual(
            missing_canonical,
            [],
            f"retired aliases point to missing canonical roots: {', '.join(missing_canonical)}",
        )
        self.assertEqual(
            resurrected,
            [],
            "retired dataset root aliases must never reappear: " + ", ".join(resurrected),
        )


if __name__ == "__main__":
    unittest.main()
