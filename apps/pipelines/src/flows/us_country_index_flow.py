from __future__ import annotations

import json
import importlib
import os
from collections.abc import Callable
from typing import Any

from src.lib.runtime_env import configure_prefect_home

configure_prefect_home()

from prefect import flow

from src.lib.db.connection import get_connection
from src.lib.runtime_env import load_project_env
from src.tasks.run_us_country_index_etl import run_us_country_index_etl


@flow(name="us-country-index")
def us_country_index_flow(**kwargs: Any) -> dict[str, object]:
    return run_us_country_index_flow(**kwargs)


def run_us_country_index_flow(**kwargs: Any) -> dict[str, object]:
    """Resolve deployment providers from MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY.

    The trusted deployment setting is ``package.module:factory``; the no-arg
    factory returns task keyword arguments including licensed providers, audited
    share reconciliation and a persistent cohort-state repository.
    """
    owned_connection = None
    try:
        load_project_env()
        if any(name not in kwargs for name in ("universe_provider", "filing_provider", "price_provider")):
            factory_path = os.getenv("MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY")
            if not factory_path:
                raise ValueError("US country-index providers are not configured; set MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY=module:factory")
            module_name, factory_name = factory_path.split(":", 1)
            configured = getattr(importlib.import_module(module_name), factory_name)()
            if not isinstance(configured, dict):
                raise ValueError("US country-index provider factory must return task keyword arguments")
            kwargs = configured | kwargs
        if "connection" not in kwargs:
            owned_connection = get_connection()
            kwargs["connection"] = owned_connection
        return run_us_country_index_etl(**kwargs)
    except Exception as exc:
        return {"status": "failed", "publication_status": "preserved", "previous_publication_preserved": True,
                "failed_stage": "configuration", "failure_summary": str(exc), "errors": [str(exc)],
                "source_errors": [], "source_warning_count": 0, "warning_count": 0, "stage_counts": {}, "reused_stages": []}
    finally:
        if owned_connection is not None:
            owned_connection.close()


def main(run_flow: Callable[[], dict[str, object]] = us_country_index_flow) -> int:
    result = run_flow()
    print(json.dumps(result, indent=2, default=str))
    return 1 if result.get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
