from src.flows.all_flows import run_all_flows


def test_run_all_flows_executes_macro_seed_then_taylor_rule(monkeypatch):
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
        "src.flows.all_flows.run_highest_ps_ranking_flow",
        lambda: calls.append("highest_ps_ranking") or {"status": "unavailable", "ranking_row_count": 0},
    )

    result = run_all_flows()

    assert calls == ["macro_seed", "taylor_rule", "currency_analysis", "highest_ps_ranking"]
    assert result == {
        "status": "success",
        "errors": [],
        "macro_seed": {"rows_loaded": 3},
        "taylor_rule": {"status": "success", "mart_rows": 2},
        "currency_analysis": {"status": "success", "ppp_snapshot_rows": 2, "irp_snapshot_rows": 3},
        "highest_ps_ranking": {"status": "unavailable", "ranking_row_count": 0},
    }


def test_run_all_flows_logs_child_flow_progress(monkeypatch, capsys):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr("src.flows.all_flows.run_taylor_rule_flow", lambda: {"status": "success"})
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})
    monkeypatch.setattr("src.flows.all_flows.run_highest_ps_ranking_flow", lambda: {"status": "unavailable"})

    run_all_flows()

    captured = capsys.readouterr()
    assert "Starting macro_seed flow..." in captured.err
    assert "Finished macro_seed flow." in captured.err
    assert "Starting taylor_rule flow..." in captured.err
    assert "Starting currency_analysis flow..." in captured.err
    assert "Starting highest_ps_ranking flow..." in captured.err


def test_run_all_flows_returns_failed_status_when_a_child_flow_reports_failed_status(monkeypatch):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr(
        "src.flows.all_flows.run_taylor_rule_flow",
        lambda: {"status": "failed", "errors": ["us_policy_rate: boom"]},
    )
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})
    monkeypatch.setattr("src.flows.all_flows.run_highest_ps_ranking_flow", lambda: {"status": "unavailable"})

    result = run_all_flows()

    assert result["status"] == "failed"
    assert result["errors"] == ["taylor_rule: us_policy_rate: boom"]
    assert result["taylor_rule"] == {"status": "failed", "errors": ["us_policy_rate: boom"]}
    assert result["highest_ps_ranking"] == {"status": "unavailable"}


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
    monkeypatch.setattr("src.flows.all_flows.run_highest_ps_ranking_flow", lambda: {"status": "failed"})

    result = run_all_flows()

    assert result["status"] == "failed"
    assert result["errors"] == [
        "taylor_rule: us_policy_rate: boom",
        "taylor_rule: eu_policy_rate: blocked",
        "highest_ps_ranking: flow failed",
    ]
