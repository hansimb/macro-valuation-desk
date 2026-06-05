from __future__ import annotations

from prefect import flow

from src.flows.currency_analysis_flow import run_currency_analysis_flow
from src.flows.macro_seed_flow import run_macro_seed_flow
from src.flows.taylor_rule_flow import run_taylor_rule_flow


def _format_flow_errors(name: str, errors: list[object]) -> str:
    bullet_lines = "\n".join(f"  - {error}" for error in errors)
    return f"{name} flow failed:\n{bullet_lines}"


def _raise_on_failed_flow(name: str, result: dict[str, object]) -> None:
    if result.get("status") != "failed":
        return

    errors = result.get("errors")
    if isinstance(errors, list):
        raise RuntimeError(_format_flow_errors(name, errors))

    raise RuntimeError(f"{name} flow failed")


def run_all_flows() -> dict[str, object]:
    macro_seed_result = run_macro_seed_flow()
    taylor_rule_result = run_taylor_rule_flow()
    currency_analysis_result = run_currency_analysis_flow()
    _raise_on_failed_flow("macro_seed", macro_seed_result)
    _raise_on_failed_flow("taylor_rule", taylor_rule_result)
    _raise_on_failed_flow("currency_analysis", currency_analysis_result)

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
