import json

from src.flows import all_flows as all_flows_module
from src.flows.all_flows import run_all_flows


def test_run_all_flows_executes_macro_seed_then_taylor_rule_then_currency_then_equity(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(
        "src.flows.all_flows.run_macro_seed_flow",
        lambda: calls.append("macro_seed") or {"rows_loaded": 3},
    )
    monkeypatch.setattr(
        "src.flows.all_flows.run_taylor_rule_flow",
        lambda: calls.append("taylor_rule") or {"status": "success", "mart_rows": 2},
    )
    monkeypatch.setattr(
        "src.flows.all_flows.run_currency_analysis_flow",
        lambda: calls.append("currency_analysis") or {"status": "success", "ppp_snapshot_rows": 2, "irp_snapshot_rows": 3},
    )
    monkeypatch.setattr(
        "src.flows.all_flows.run_equity_market_valuation_flow",
        lambda: calls.append("equity_market_valuation") or {"status": "success", "mart_rows": 14},
    )

    result = run_all_flows()

    assert calls == ["macro_seed", "taylor_rule", "currency_analysis", "equity_market_valuation"]
    assert result == {
        "status": "success",
        "errors": [],
        "macro_seed": {"rows_loaded": 3},
        "taylor_rule": {"status": "success", "mart_rows": 2},
        "currency_analysis": {"status": "success", "ppp_snapshot_rows": 2, "irp_snapshot_rows": 3},
        "equity_market_valuation": {"status": "success", "mart_rows": 14},
    }


def test_run_all_flows_logs_child_flow_progress(monkeypatch, capsys):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr("src.flows.all_flows.run_taylor_rule_flow", lambda: {"status": "success"})
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})
    monkeypatch.setattr("src.flows.all_flows.run_equity_market_valuation_flow", lambda: {"status": "success"})

    run_all_flows()

    captured = capsys.readouterr()
    assert "Starting macro_seed flow..." in captured.err
    assert "Finished macro_seed flow." in captured.err
    assert "Starting taylor_rule flow..." in captured.err
    assert "Starting currency_analysis flow..." in captured.err
    assert "Starting equity_market_valuation flow..." in captured.err
    assert "highest_ps_ranking" not in captured.err


def test_run_all_flows_returns_failed_status_when_a_child_flow_reports_failed_status(monkeypatch):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr(
        "src.flows.all_flows.run_taylor_rule_flow",
        lambda: {"status": "failed", "errors": ["us_policy_rate: boom"]},
    )
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})
    monkeypatch.setattr("src.flows.all_flows.run_equity_market_valuation_flow", lambda: {"status": "success"})

    result = run_all_flows()

    assert result["status"] == "failed"
    assert result["errors"] == ["taylor_rule: us_policy_rate: boom"]
    assert result["taylor_rule"] == {"status": "failed", "errors": ["us_policy_rate: boom"]}
    assert "highest_ps_ranking" not in result


def test_run_all_flows_collects_multiple_child_flow_errors(monkeypatch):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr(
        "src.flows.all_flows.run_taylor_rule_flow",
        lambda: {
            "status": "failed",
            "errors": ["us_policy_rate: boom", "eu_policy_rate: blocked"],
        },
    )
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})
    monkeypatch.setattr(
        "src.flows.all_flows.run_equity_market_valuation_flow",
        lambda: {"status": "failed", "errors": ["norway_large_cap: provider unavailable"]},
    )

    result = run_all_flows()

    assert result["status"] == "failed"
    assert result["errors"] == [
        "taylor_rule: us_policy_rate: boom",
        "taylor_rule: eu_policy_rate: blocked",
        "equity_market_valuation: norway_large_cap: provider unavailable",
    ]


def test_run_all_flows_prefers_child_failure_summary_when_available(monkeypatch):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr("src.flows.all_flows.run_taylor_rule_flow", lambda: {"status": "success"})
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})
    monkeypatch.setattr(
        "src.flows.all_flows.run_equity_market_valuation_flow",
        lambda: {
            "status": "failed",
            "failure_summary": "Equity market valuation ETL failed for all 14 markets; first error: missing token.",
            "errors": ["us_total_market: missing token", "us_large_cap: missing token"],
        },
    )

    result = run_all_flows()

    assert result["status"] == "failed"
    assert result["errors"] == [
        "equity_market_valuation: Equity market valuation ETL failed for all 14 markets; first error: missing token."
    ]


def test_all_flows_cli_prints_result_and_exits_nonzero_when_flow_status_failed(capsys):
    result = {
        "status": "failed",
        "errors": ["equity_market_valuation: missing token"],
    }

    exit_code = all_flows_module.main(lambda: result)

    captured = capsys.readouterr()
    assert json.loads(captured.out) == result
    assert exit_code == 1
