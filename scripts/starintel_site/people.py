from __future__ import annotations

import shutil
from pathlib import Path


def build_people_directory(input_root: Path, output: Path, assets: Path) -> dict[str, int]:
    """Keep the generated people directory disabled.

    Building a public profile page for every person duplicated too much of the
    corpus and made CI and deployment builds unacceptably slow. Canonical person
    records remain available through the normal dataset and document outputs.
    """
    del input_root, assets

    people_output = output / "people"
    if people_output.exists():
        shutil.rmtree(people_output)

    asset_output = output / "assets"
    for filename in ("people.css", "people.js"):
        path = asset_output / filename
        if path.exists():
            path.unlink()

    return {"people": 0, "alumni": 0}
