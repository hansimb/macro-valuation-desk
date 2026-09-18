from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from src.flows.us_country_index_backfill import BackfillConfigurationError, main, run_backfill
from src.flows.us_country_index_flow import run_us_country_index_flow
from src.lib.source.country_index_types import DailyPrice, ProviderLicense, RegulatoryFiling, RawXbrlFact
from src.lib.source.adapters.sec_xbrl import SecXbrlResult

from test_us_country_index_flow import Database, Filings, Prices, Universe


METRICS = ("pe", "pb", "ps", "pcf", "pfcf", "dividend_yield")


class StatefulCohorts:
    def __init__(self):
        self.state = None

    def checkpoint_config(self):
        return {"fixture": "task-13-stateful-cohorts-v1"}

    def load(self, **_kwargs):
        if self.state is None:
            return None
        state = dict(self.state)
        if _kwargs["week"] == date(2026, 3, 16):
            state["forced_replacements"] = {"C": "D"}
        return state

    def save(self, *, state, **_kwargs):
        self.state = state


class AmendmentFilings(Filings):
    def checkpoint_config(self):
        return {"fixture": "task-13-amendment-v1"}

    def fetch_companyfacts(self, cik):
        result = super().fetch_companyfacts(cik)
        if cik != "A":
            return result
        original = next(f for f in result.facts if f.concept_name == "NetIncomeLossAvailableToCommonStockholdersBasic")
        amendment_time = datetime(2026, 3, 10, 12, tzinfo=UTC)
        amended_filing = RegulatoryFiling(
            "sec", "A-amendment", "hash-A-amendment", "us", "A", "10-K/A",
            "fixture://filing/A-amendment", {"cik": "A", "amendment": True}, amendment_time,
            published_at=amendment_time, amendment_of_external_id="A",
        )
        amended_fact = replace(
            original,
            filing_id="A-amendment",
            filing_content_hash="hash-A-amendment",
            fact_id="A-NetIncomeLossAvailableToCommonStockholdersBasic-amended",
            value_text="8",
            published_at=amendment_time,
        )
        return SecXbrlResult(
            ok=True,
            filings=(*result.filings, amended_filing),
            facts=(*result.facts, amended_fact),
        )


class CorporateActionPrices(Prices):
    license = ProviderLicense("fixture_development", "development_only", "fixture://terms")

    def __init__(self):
        super().__init__()
        self.week = None

    def checkpoint_config(self):
        return {"fixture": "task-13-corporate-actions-v1", "week": self.week}

    def daily_prices(self, security, start, end):
        self.week = start
        rows = super().daily_prices(security, start, end)
        adjusted = []
        for row in rows:
            if start == date(2026, 3, 9) and security.security_id == "A" and row.trading_date >= date(2026, 3, 10):
                row = replace(
                    row,
                    close_price=row.close_price / Decimal(2),
                    split_adjusted_close_price=row.close_price / Decimal(2),
                    adjustment_metadata={"split_date": "2026-03-10", "split_ratio": "2:1"},
                )
            if start == date(2026, 3, 9) and security.security_id == "A" and row.trading_date == date(2026, 3, 11):
                continue
            if start == date(2026, 3, 16) and row.trading_date == date(2026, 3, 20):
                continue
            adjusted.append(row)
        return adjusted


class RealAcceptanceFixture:
    """Runs the real Task 10 flow with deterministic source and DB fixtures."""

    receipt_source_provenance = "fixture:task-13-real-task10-v2"

    def __init__(self):
        self.calls: list[dict[str, object]] = []
        self.databases: list[Database] = []
        self.universe = Universe()
        self.filings = AmendmentFilings()
        self.prices = CorporateActionPrices()
        self.cohorts = StatefulCohorts()

    def __call__(self, **kwargs):
        week = kwargs["valuation_week"]
        self.calls.append(kwargs)
        database = Database()
        self.databases.append(database)
        self.prices.week = week
        run_id = f"acceptance-{week.isoformat()}"
        result = run_us_country_index_flow(
            connection=database,
            universe_provider=self.universe,
            filing_provider=self.filings,
            price_provider=self.prices,
            share_state=lambda listing, day, pit, price: {
                "shares_outstanding": Decimal(2) if listing.security_id == "A" and day >= date(2026, 3, 10) else Decimal(1),
                "industry": "other",
                "revenue_comparable": True,
                "source": "fixture://split-reconciled-shares",
            },
            cohort_state=self.cohorts,
            clock=lambda: datetime.combine(week + timedelta(days=7), datetime.min.time(), UTC),
            run_id=run_id,
            checkpoint_dir=kwargs["checkpoint_dir"],
            methodology_version=kwargs["methodology_version"],
            environment="development",
            sensitivity_draws=8,
        )
        if result["status"] == "success":
            checkpoint = kwargs["checkpoint_dir"] / f"{run_id}.validation.json"
            import json
            envelope = json.loads(checkpoint.read_text(encoding="utf-8"))
            result["backfill_provenance"] = {
                "task_checkpoint": str(checkpoint.resolve()),
                "task_checkpoint_fingerprint": envelope["fingerprint"],
            }
        rows = [
            row for row in database.rows.get("core.country_weekly_metrics", {}).values()
            if row["run_id"] == run_id
        ]
        result["weekly_rows"] = sorted(
            ({key: row[key] for key in ("run_id", "methodology_version", "week_id", "metric_key", "metric_value", "daily_observation_count", "cohort_version")} for row in rows),
            key=lambda row: row["metric_key"],
        )
        return result


def test_fixture_backfill_covers_acceptance_boundaries_and_is_idempotent(tmp_path):
    fixture = RealAcceptanceFixture()
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

    assert first["status"] == second["status"] == "success", (first, second)
    assert first["weekly_rows"] == second["weekly_rows"]
    assert len(first["weekly_rows"]) == 18
    assert first["weeks"] == ["2026-03-02", "2026-03-09", "2026-03-16"]
    assert all(row["methodology_version"] == "us-country-index-v1" for row in first["weekly_rows"])
    by_week = {}
    for row in first["weekly_rows"]:
        by_week.setdefault(row["week_id"], []).append(row)
    assert {row["daily_observation_count"] for row in by_week["2026-03-02"]} == {5}
    assert {row["daily_observation_count"] for row in by_week["2026-03-16"]} == {4}
    assert {row["cohort_version"] for row in by_week["2026-03-02"]} == {"2026-03-02"}
    assert {row["cohort_version"] for row in by_week["2026-03-16"]} == {"2026-03-16"}
    first_pe = next(row["metric_value"] for row in by_week["2026-03-02"] if row["metric_key"] == "pe")
    amended_pe = next(row["metric_value"] for row in by_week["2026-03-09"] if row["metric_key"] == "pe")
    assert first_pe != amended_pe
    assert all(len(database.rows["core.country_weekly_metrics"]) == 6 for database in fixture.databases)
    assert all(next(iter(database.rows["core.country_index_runs"].values()))["run_status"] == "completed" for database in fixture.databases)
    amendment_week = fixture.databases[1]
    pit = amendment_week.rows["core.point_in_time_fundamentals"]
    assert pit[("A", date(2026, 3, 9), "us-country-index-v1")]["ttm_net_income"] == Decimal(4)
    assert pit[("A", date(2026, 3, 10), "us-country-index-v1")]["ttm_net_income"] == Decimal(8)
    assert any(key[1] == "A-amendment" for key in amendment_week.rows["raw.regulatory_filings"])
    price_rows = [row for database in fixture.databases for row in database.rows["raw.security_prices"].values()]
    assert any(row["adjustment_metadata"].get("split_ratio") == "2:1" for row in price_rows)
    assert not any(row["security_id"] == "A" and row["trading_date"] == date(2026, 3, 11) for row in price_rows)
    final_members = {row["security_id"] for row in fixture.databases[2].rows["core.country_cohort_members"].values()}
    assert final_members == {"A", "B", "D"}
    assert len(fixture.calls) == 3, "resume must use receipts rather than republish superseded Task 10 runs"
    assert all(call["market"] == "us" for call in fixture.calls)
    assert all(call["resume"] is True for call in fixture.calls)
    assert all(call["development_prices"] is True for call in fixture.calls)


def test_backfill_refuses_unbounded_reversed_and_partial_week_ranges(tmp_path):
    fixture = RealAcceptanceFixture()
    common = dict(market="us", resume=False, development_prices=True, checkpoint_dir=tmp_path, flow_runner=fixture)

    with pytest.raises(BackfillConfigurationError, match="bounded"):
        run_backfill(from_date=None, to_date=date(2026, 3, 20), **common)
    with pytest.raises(BackfillConfigurationError, match="before"):
        run_backfill(from_date=date(2026, 3, 20), to_date=date(2026, 3, 2), **common)
    with pytest.raises(BackfillConfigurationError, match="complete Monday-Friday"):
        run_backfill(from_date=date(2026, 3, 3), to_date=date(2026, 3, 20), **common)


def test_backfill_refuses_non_us_market_and_production_development_prices(tmp_path):
    fixture = RealAcceptanceFixture()

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
    assert main(["--market", "us"], flow_runner=RealAcceptanceFixture()) == 2

    def failing(**kwargs):
        return {"status": "failed", "failure_summary": "fixture source failed", "weekly_rows": ()}

    code = main(
        ["--from", "2026-03-02", "--to", "2026-03-20", "--market", "us", "--development-prices"],
        flow_runner=failing,
        checkpoint_dir=tmp_path,
    )
    assert code == 1
    assert "fixture source failed" in capsys.readouterr().out


def test_development_receipt_cannot_satisfy_production_resume(tmp_path):
    development = RealAcceptanceFixture()
    assert run_backfill(
        date(2026, 3, 2),
        date(2026, 3, 6),
        market="us",
        resume=True,
        development_prices=True,
        environment="development",
        checkpoint_dir=tmp_path,
        flow_runner=development,
    )["status"] == "success"

    production_calls = []

    def production_guard(**kwargs):
        production_calls.append(kwargs)
        return {
            "status": "failed",
            "failure_summary": "development-only prices cannot be published in production",
            "weekly_rows": (),
        }

    production_guard.receipt_source_provenance = development.receipt_source_provenance
    resumed = run_backfill(
        date(2026, 3, 2),
        date(2026, 3, 6),
        market="us",
        resume=True,
        development_prices=False,
        environment="production",
        checkpoint_dir=tmp_path,
        flow_runner=production_guard,
    )

    assert resumed["status"] == "failed"
    assert "development-only" in resumed["failure_summary"]
    assert len(production_calls) == 1, "production must execute its license guard instead of reading a development receipt"
