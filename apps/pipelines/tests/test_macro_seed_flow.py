from src.flows.macro_seed_flow import run_macro_seed_flow


def test_macro_seed_flow_returns_summary():
    result = run_macro_seed_flow()

    assert result["rows_loaded"] >= 1
