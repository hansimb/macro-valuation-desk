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

    result = run_all_flows()

    assert calls == ["macro_seed", "taylor_rule", "currency_analysis"]
    assert result == {
        "macro_seed": {"rows_loaded": 3},
        "taylor_rule": {"status": "success", "mart_rows": 2},
        "currency_analysis": {"status": "success", "ppp_snapshot_rows": 2, "irp_snapshot_rows": 3},
    }


def test_run_all_flows_raises_when_a_child_flow_reports_failed_status(monkeypatch):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr(
        "src.flows.all_flows.run_taylor_rule_flow",
        lambda: {"status": "failed", "errors": ["us_policy_rate: boom"]},
    )
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})

    try:
        run_all_flows()
    except RuntimeError as error:
        assert str(error) == "taylor_rule flow failed:\n  - us_policy_rate: boom"
    else:
        raise AssertionError("expected run_all_flows() to raise for failed child flow")


def test_run_all_flows_formats_multiple_errors_as_bulleted_lines(monkeypatch):
    monkeypatch.setattr("src.flows.all_flows.run_macro_seed_flow", lambda: {"rows_loaded": 3})
    monkeypatch.setattr(
        "src.flows.all_flows.run_taylor_rule_flow",
        lambda: {
            "status": "failed",
            "errors": ["us_policy_rate: boom", "eu_policy_rate: blocked"],
        },
    )
    monkeypatch.setattr("src.flows.all_flows.run_currency_analysis_flow", lambda: {"status": "success"})

    try:
        run_all_flows()
    except RuntimeError as error:
        assert str(error) == (
            "taylor_rule flow failed:\n"
            "  - us_policy_rate: boom\n"
            "  - eu_policy_rate: blocked"
        )
    else:
        raise AssertionError("expected run_all_flows() to raise for failed child flow")
