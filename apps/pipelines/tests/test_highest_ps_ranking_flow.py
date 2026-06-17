from src.flows.highest_ps_ranking_flow import run_highest_ps_ranking_flow


def test_run_highest_ps_ranking_flow_builds_and_writes_usa_section(monkeypatch):
    candidate_rows = [
        {
            "section_key": "usa",
            "section_label": "USA High P/S Leaders",
            "universe_key": "sp500",
            "universe_label": "S&P 500",
            "as_of_date": "2026-06-15",
            "ticker": "NVDA",
            "company": "NVIDIA",
            "country_code": "US",
            "country_name": "United States",
            "sector": "Information Technology",
            "market_cap": 3100.0,
            "average_daily_traded_value": 52000.0,
            "ps_ratio": 24.10,
            "index_weight_pct": 6.10,
        },
        {
            "section_key": "usa",
            "section_label": "USA High P/S Leaders",
            "universe_key": "sp500",
            "universe_label": "S&P 500",
            "as_of_date": "2026-06-15",
            "ticker": "MSFT",
            "company": "Microsoft",
            "country_code": "US",
            "country_name": "United States",
            "sector": "Information Technology",
            "market_cap": 3200.0,
            "average_daily_traded_value": 21000.0,
            "ps_ratio": 12.00,
            "index_weight_pct": 6.50,
        },
        {
            "section_key": "usa",
            "section_label": "USA High P/S Leaders",
            "universe_key": "sp500",
            "universe_label": "S&P 500",
            "as_of_date": "2026-06-15",
            "ticker": "V",
            "company": "Visa",
            "country_code": "US",
            "country_name": "United States",
            "sector": "Financials",
            "market_cap": 540.0,
            "average_daily_traded_value": 9000.0,
            "ps_ratio": 16.00,
            "index_weight_pct": 1.10,
        },
        {
            "section_key": "usa",
            "section_label": "USA High P/S Leaders",
            "universe_key": "sp500",
            "universe_label": "S&P 500",
            "as_of_date": "2026-06-15",
            "ticker": "AAPL",
            "company": "Apple",
            "country_code": "US",
            "country_name": "United States",
            "sector": "Information Technology",
            "market_cap": 2900.0,
            "average_daily_traded_value": 18000.0,
            "ps_ratio": 8.00,
            "index_weight_pct": 6.00,
        },
    ]

    captured = {}

    monkeypatch.setattr("src.flows.highest_ps_ranking_flow.get_connection", lambda: object())
    monkeypatch.setattr("src.flows.highest_ps_ranking_flow.bootstrap_taylor_rule_schema", lambda _connection: None)
    monkeypatch.setattr("src.flows.highest_ps_ranking_flow.read_highest_ps_candidate_rows", lambda _connection: candidate_rows)
    monkeypatch.setattr(
        "src.tasks.load_highest_ps_ranking_layers.load_highest_ps_ranking_layers",
        lambda connection, **kwargs: captured.setdefault("payload", kwargs) or {
            "section_summary_rows": len(kwargs["section_summary_rows"]),
            "ranking_rows": len(kwargs["section_ranking_rows"]),
        },
    )

    result = run_highest_ps_ranking_flow()

    assert result["status"] == "success"
    assert result["section_count"] == 1
    assert result["ranking_row_count"] == 2
    assert captured["payload"]["section_summary_rows"][0]["section_key"] == "usa"
    assert len(captured["payload"]["section_ranking_rows"]) == 2


def test_run_highest_ps_ranking_flow_returns_unavailable_when_no_candidates_exist(monkeypatch):
    captured = {}

    monkeypatch.setattr("src.flows.highest_ps_ranking_flow.get_connection", lambda: object())
    monkeypatch.setattr("src.flows.highest_ps_ranking_flow.bootstrap_taylor_rule_schema", lambda _connection: None)
    monkeypatch.setattr("src.flows.highest_ps_ranking_flow.read_highest_ps_candidate_rows", lambda _connection: [])
    monkeypatch.setattr(
        "src.tasks.load_highest_ps_ranking_layers.load_highest_ps_ranking_layers",
        lambda connection, **kwargs: captured.setdefault("payload", kwargs) or {
            "section_summary_rows": len(kwargs["section_summary_rows"]),
            "ranking_rows": len(kwargs["section_ranking_rows"]),
        },
    )

    result = run_highest_ps_ranking_flow()

    assert result["status"] == "unavailable"
    assert result["section_count"] == 1
    assert result["ranking_row_count"] == 0
    assert captured["payload"]["section_summary_rows"][0]["section_key"] == "usa"
    assert captured["payload"]["section_summary_rows"][0]["unavailable"] is True
    assert captured["payload"]["section_ranking_rows"] == []
