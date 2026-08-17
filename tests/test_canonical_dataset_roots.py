from pathlib import Path


def test_flock_uses_single_canonical_dataset_root() -> None:
    digs = Path("digs")
    canonical = digs / "flock"
    aliases = sorted(
        path.name
        for path in digs.iterdir()
        if path.is_dir() and path.name.startswith("flock-")
    )

    assert canonical.is_dir(), "Flock research must live under digs/flock/"
    assert aliases == [], (
        "Flock research must not create sibling dataset roots; move these under "
        f"digs/flock/: {', '.join(aliases)}"
    )
