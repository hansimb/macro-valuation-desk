from __future__ import annotations

from prefect import flow

from src.flows.currency_analysis_flow import run_currency_analysis_flow
from src.flows.macro_seed_flow import run_macro_seed_flow
from src.flows.taylor_rule_flow import run_taylor_rule_flow
from src.lib.pipeline.error_handling import raise_on_failed_flow


def run_all_flows() -> dict[str, object]:
    macro_seed_result = run_macro_seed_flow()
    taylor_rule_result = run_taylor_rule_flow()
    currency_analysis_result = run_currency_analysis_flow()
    raise_on_failed_flow("macro_seed", macro_seed_result)
    raise_on_failed_flow("taylor_rule", taylor_rule_result)
    raise_on_failed_flow("currency_analysis", currency_analysis_result)

    return {
        "macro_seed": macro_seed_result,
        "taylor_rule": taylor_rule_result,
        "currency_analysis": currency_analysis_result,
    }


@flow(name="all-flows")
def all_flows() -> dict[str, object]:
    return run_all_flows()


if __name__ == "__main__":
    all_flows()
