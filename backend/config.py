"""Auto Dig typed backend API configuration.

All configuration is environment-driven. No secrets are ever logged or
embedded in responses. The backend is a private control-plane service:
it fronts the Auto Dig runtime and the StarIntel server; browsers never
receive database, queue, or management credentials.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


@dataclass(frozen=True)
class BackendConfig:
    root: Path = field(default_factory=lambda: Path(os.environ.get("AUTO_DIG_ROOT", Path.cwd())))
    state_dir: Path = field(default_factory=lambda: Path(os.environ.get("AUTO_DIG_STATE_DIR", "backend-state")))
    server_url: str = field(default_factory=lambda: os.environ.get("STARINTEL_SERVER_URL", "http://127.0.0.1:5000"))
    server_token: str | None = field(default_factory=lambda: os.environ.get("STARINTEL_TOKEN") or None)
    server_timeout: float = field(default_factory=lambda: float(os.environ.get("STARINTEL_TIMEOUT", "10")))
    max_batch_documents: int = field(default_factory=lambda: _int_env("STARINTEL_BULK_MAX", 200))

    @property
    def digs_root(self) -> Path:
        return self.root / "digs"

    @property
    def db_root(self) -> Path:
        return self.root / "db"

    @property
    def runs_state_root(self) -> Path:
        return self.state_dir / "runs"

    def resolve_state_path(self, run_id: str) -> Path:
        if "/" in run_id or run_id.startswith("."):
            raise ValueError("invalid run id")
        return self.runs_state_root / f"{run_id}.json"


def load_config() -> BackendConfig:
    return BackendConfig()
