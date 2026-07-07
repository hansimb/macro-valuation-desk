from __future__ import annotations

import sys
from collections.abc import Callable

from src.lib.runtime_env import configure_prefect_home

configure_prefect_home()

from prefect import flow

from src.flows.currency_analysis_flow import run_currency_analysis_flow
from src.flows.equity_market_valuation_flow import run_equity_market_valuation_flow
from src.flows.macro_seed_flow import run_macro_seed_flow
from src.flows.taylor_rule_flow import run_taylor_rule_flow


def _collect_child_flow_errors(name: str, result: dict[str, object]) -> list[str]:
    if result.get("status") != "failed":
        return []

    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        return [f"{name}: {error}" for error in errors]

    return [f"{name}: flow failed"]


def _run_child_flow(name: str, run_flow: Callable[[], dict[str, object]]) -> dict[str, object]:
    print(f"Starting {name} flow...", file=sys.stderr, flush=True)
    result = run_flow()
    print(f"Finished {name} flow.", file=sys.stderr, flush=True)
    return result


def run_all_flows() -> dict[str, object]:
    macro_seed_result = _run_child_flow("macro_seed", run_macro_seed_flow)
    taylor_rule_result = _run_child_flow("taylor_rule", run_taylor_rule_flow)
    currency_analysis_result = _run_child_flow("currency_analysis", run_currency_analysis_flow)
    equity_market_valuation_result = _run_child_flow(
        "equity_market_valuation",
        run_equity_market_valuation_flow,
    )

    errors = [
        *(_collect_child_flow_errors("macro_seed", macro_seed_result)),
        *(_collect_child_flow_errors("taylor_rule", taylor_rule_result)),
        *(_collect_child_flow_errors("currency_analysis", currency_analysis_result)),
        *(_collect_child_flow_errors("equity_market_valuation", equity_market_valuation_result)),
    ]

    return {
        "status": "failed" if errors else "success",
        "errors": errors,
        "macro_seed": macro_seed_result,
        "taylor_rule": taylor_rule_result,
        "currency_analysis": currency_analysis_result,
        "equity_market_valuation": equity_market_valuation_result,
    }


@flow(name="all-flows")
def all_flows() -> dict[str, object]:
    return run_all_flows()


if __name__ == "__main__":
    all_flows()
