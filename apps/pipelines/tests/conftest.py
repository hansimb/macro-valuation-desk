from __future__ import annotations

import os
from pathlib import Path


TEST_PREFECT_HOME = Path(__file__).resolve().parents[1] / ".prefect-test-home"
TEST_PREFECT_HOME.mkdir(exist_ok=True)
os.environ.setdefault("PREFECT_HOME", str(TEST_PREFECT_HOME))
