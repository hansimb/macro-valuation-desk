from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from src.lib.runtime_env import configure_prefect_home

configure_prefect_home()

from prefect import flow

from src.lib.db.connection import get_connection
from src.tasks.run_us_country_index_etl import run_us_country_index_etl


@flow(name="us-country-index")
def us_country_index_flow(**kwargs: Any) -> dict[str, object]:
    return run_us_country_index_flow(**kwargs)


def run_us_country_index_flow(**kwargs: Any) -> dict[str, object]:
    if "connection" not in kwargs:
        kwargs["connection"] = get_connection()
    return run_us_country_index_etl(**kwargs)


def main(run_flow: Callable[[], dict[str, object]] = us_country_index_flow) -> int:
    result = run_flow()
    print(json.dumps(result, indent=2, default=str))
    return 1 if result.get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
