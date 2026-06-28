from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def test_all_flows_configures_project_prefect_home(monkeypatch):
    monkeypatch.delenv("PREFECT_HOME", raising=False)
    monkeypatch.delenv("PREFECT_PROFILES_PATH", raising=False)
    sys.modules.pop("src.flows.all_flows", None)

    importlib.import_module("src.flows.all_flows")

    expected_home = Path(__file__).resolve().parents[1] / ".prefect-home"
    assert Path(os.environ["PREFECT_HOME"]) == expected_home
    assert Path(os.environ["PREFECT_PROFILES_PATH"]) == expected_home / "profiles.toml"
    assert expected_home.exists()
