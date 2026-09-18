from __future__ import annotations

from datetime import date

import pytest

from src.flows.us_country_index_backfill import BackfillConfigurationError, main, run_backfill


class AcceptanceFixture:
    """Deterministic boundary fixture; Task 10 owns the calculation internals."""

    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs):
        week = kwargs["valuation_week"]
        self.calls.append(kwargs)
        events = {
            date(2026, 3, 2): ("original_filing", "pre_split", "five_day_week", "cohort_v1"),
            date(2026, 3, 9): ("amended_filing_visible", "split_2_for_1", "missing_price_day", "cohort_v1"),
            date(2026, 3, 16): ("amended_filing_visible", "post_split", "holiday_four_day_week", "cohort_v2"),
        }[week]
        rows = tuple(
            (kwargs["methodology_version"], week.isoformat(), metric, events)
            for metric in ("pe", "pb", "ps", "pcf", "pfcf", "dividend_yield")
        )
        return {
            "status": "success",
            "publication_status": "published",
            "weekly_rows": rows,
            "fixture_events": events,
            "stage_counts": {"weekly_summaries": 6},
            "reused_stages": ["immutable_acquisition"] if kwargs["resume"] else [],
        }


def test_fixture_backfill_covers_acceptance_boundaries_and_is_idempotent(tmp_path):
    fixture = AcceptanceFixture()
    arguments = dict(
        from_date=date(2026, 3, 2),
        to_date=date(2026, 3, 20),
        market="us",
        resume=True,
        development_prices=True,
        checkpoint_dir=tmp_path,
        flow_runner=fixture,
    )

    first = run_backfill(**arguments)
    second = run_backfill(**arguments)

    assert first["status"] == second["status"] == "success"
    assert first["weekly_rows"] == second["weekly_rows"]
    assert len(first["weekly_rows"]) == 18
    assert first["weeks"] == ["2026-03-02", "2026-03-09", "2026-03-16"]
    observed = {event for row in first["weekly_rows"] for event in row[3]}
    assert {
        "original_filing",
        "amended_filing_visible",
        "split_2_for_1",
        "missing_price_day",
        "cohort_v1",
        "cohort_v2",
        "holiday_four_day_week",
    } <= observed
    assert all(call["market"] == "us" for call in fixture.calls)
    assert all(call["resume"] is True for call in fixture.calls)
    assert all(call["development_prices"] is True for call in fixture.calls)


def test_backfill_refuses_unbounded_reversed_and_partial_week_ranges(tmp_path):
    fixture = AcceptanceFixture()
    common = dict(market="us", resume=False, development_prices=True, checkpoint_dir=tmp_path, flow_runner=fixture)

    with pytest.raises(BackfillConfigurationError, match="bounded"):
        run_backfill(from_date=None, to_date=date(2026, 3, 20), **common)
    with pytest.raises(BackfillConfigurationError, match="before"):
        run_backfill(from_date=date(2026, 3, 20), to_date=date(2026, 3, 2), **common)
    with pytest.raises(BackfillConfigurationError, match="complete Monday-Friday"):
        run_backfill(from_date=date(2026, 3, 3), to_date=date(2026, 3, 20), **common)


def test_backfill_refuses_non_us_market_and_production_development_prices(tmp_path):
    fixture = AcceptanceFixture()

    with pytest.raises(BackfillConfigurationError, match="only --market us"):
        run_backfill(date(2026, 3, 2), date(2026, 3, 20), market="fi", checkpoint_dir=tmp_path, flow_runner=fixture)
    with pytest.raises(BackfillConfigurationError, match="production"):
        run_backfill(
            date(2026, 3, 2),
            date(2026, 3, 20),
            market="us",
            environment="production",
            development_prices=True,
            checkpoint_dir=tmp_path,
            flow_runner=fixture,
        )


def test_cli_requires_bounds_and_returns_failure_when_a_week_fails(tmp_path, capsys):
    assert main(["--market", "us"], flow_runner=AcceptanceFixture()) == 2

    def failing(**kwargs):
        return {"status": "failed", "failure_summary": "fixture source failed", "weekly_rows": ()}

    code = main(
        ["--from", "2026-03-02", "--to", "2026-03-20", "--market", "us", "--development-prices"],
        flow_runner=failing,
        checkpoint_dir=tmp_path,
    )
    assert code == 1
    assert "fixture source failed" in capsys.readouterr().out
