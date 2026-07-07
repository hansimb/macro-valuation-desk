from __future__ import annotations

from src.lib.runtime_env import configure_prefect_home

configure_prefect_home()

from prefect import flow

from src.lib.db import get_connection
from src.lib.pipeline.equity_market_universe import EQUITY_MARKET_UNIVERSE
from src.lib.source.adapters.eodhd import EodhdAdapter
from src.tasks import run_equity_market_valuation_etl as etl_module


def _call_task(task_or_fn, *args, **kwargs):
    if hasattr(task_or_fn, "fn"):
        return task_or_fn.fn(*args, **kwargs)

    return task_or_fn(*args, **kwargs)


def run_equity_market_valuation_flow() -> dict[str, object]:
    connection = get_connection()
    return _call_task(
        etl_module.run_equity_market_valuation_etl,
        connection,
        definitions=EQUITY_MARKET_UNIVERSE,
        adapter_factories={"eodhd": EodhdAdapter},
    )


@flow(name="equity-market-valuation-flow")
def equity_market_valuation_flow() -> dict[str, object]:
    return run_equity_market_valuation_flow()


if __name__ == "__main__":
    equity_market_valuation_flow()
