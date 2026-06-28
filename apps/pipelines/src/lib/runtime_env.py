from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def load_project_env() -> None:
    root = Path(__file__).resolve().parents[4]
    load_env_file(root / ".env")
    load_env_file(root / "infra" / "compose" / ".env")


def configure_prefect_home() -> None:
    prefect_home = Path(__file__).resolve().parents[2] / ".prefect-home"
    prefect_home.mkdir(exist_ok=True)
    os.environ.setdefault("PREFECT_HOME", str(prefect_home))
    os.environ.setdefault("PREFECT_PROFILES_PATH", str(prefect_home / "profiles.toml"))
