from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal as D
import importlib
import json
import re

import pytest

from src.lib.source.adapters.sec_xbrl import SecXbrlResult
from src.lib.source.country_index_types import DailyPrice, ProviderLicense, RawXbrlFact, RegulatoryFiling, SecurityListing


WEEK = date(2026, 9, 7)
NOW = datetime(2026, 9, 14, 8, tzinfo=UTC)
STAGES = ["immutable_acquisition", "normalization_point_in_time", "eligible_universe_prices_fx", "cohort_evaluation", "daily_calculations", "weekly_summaries", "sensitivity", "validation", "persistence_publication"]


class Database:
    """Transactional schema recorder; executes the real Task 9 writers and publisher."""
    def __init__(self):
        self.rows = {}
        self.publication = "previous-run"
        self.events = []
        self.fail_publish = False

    @contextmanager
    def transaction(self):
        snapshot = deepcopy((self.rows, self.publication))
        self.events.append("begin")
        try:
            yield
        except BaseException:
            self.rows, self.publication = snapshot
            self.events.append("rollback")
            raise
        else:
            self.events.append("commit")

    def cursor(self):
        return Cursor(self)


class Cursor:
    def __init__(self, db):
        self.db = db
        self.query = ""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def executemany(self, query, rows):
        table = re.search(r"insert into ([\w.]+)", query).group(1)
        keys = re.search(r"on conflict \(([^)]+)\)", query).group(1).replace(" ", "").split(",")
        for original in rows:
            row = dict(original)
            for key in ("source_coverage", "structured_reasons", "source_lineage", "content_json", "dimensions_json", "adjustment_metadata", "membership_reason", "structured_reason"):
                if key in row:
                    row[key] = json.loads(row[key])
            self.db.rows.setdefault(table, {})[tuple(row[k] for k in keys)] = row

    def execute(self, query, params=None):
        self.query = " ".join(query.split()).lower()
        if self.query.startswith("insert into marts.country_index_publications"):
            if self.db.fail_publish:
                raise RuntimeError("injected pointer failure")
            self.db.publication = params["run_id"]
            self.db.events.append("publish")

    def fetchone(self):
        if "for update" in self.query and "core.country_index_runs" in self.query:
            return next(iter(self.db.rows["core.country_index_runs"].values()))
        return None

    def fetchall(self):
        for table in ("core.country_daily_metrics", "core.country_weekly_metrics"):
            if table in self.query:
                return list(self.db.rows.get(table, {}).values())
        return []


class Universe:
    def __init__(self):
        self.calls = 0
        self.listings = [SecurityListing(f"l-{s}", s, s, s, "common_stock", "us", "XNAS", s, "USD", date(2020, 1, 1), "active", "fixture", s) for s in ("A", "B", "C", "D")]

    def listings_as_of(self, market_id, as_of):
        self.calls += 1
        return self.listings


class Filings:
    def __init__(self):
        self.calls = []
        self.failed = set()

    def fetch_companyfacts(self, cik):
        self.calls.append(cik)
        if cik in self.failed:
            return SecXbrlResult.failure(cik=cik, url="fixture://filing", error_type="fetch_error", message="exact source outage")
        publication = datetime(2026, 2, 1, tzinfo=UTC)
        filing = RegulatoryFiling("sec", cik, f"hash-{cik}", "us", cik, "10-K", "fixture://filing", {"cik": cik}, NOW, published_at=publication)
        concepts = {"RevenueFromContractWithCustomerExcludingAssessedTax": "40", "NetIncomeLossAvailableToCommonStockholdersBasic": "4", "NetCashProvidedByUsedInOperatingActivities": "8", "PaymentsToAcquirePropertyPlantAndEquipment": "2", "PaymentsOfDividendsCommonStock": "1", "CommonStockholdersEquity": "20", "CommonStockSharesOutstanding": "1"}
        facts = []
        for concept, value in concepts.items():
            instant = concept in {"CommonStockholdersEquity", "CommonStockSharesOutstanding"}
            facts.append(RawXbrlFact("sec", cik, filing.content_hash, f"{cik}-{concept}", "us-gaap", concept, value, publication, security_id=cik, unit="shares" if "SharesOutstanding" in concept else "USD", instant_date=date(2025, 12, 31) if instant else None, period_start=None if instant else date(2025, 1, 1), period_end=None if instant else date(2025, 12, 31), is_consolidated=True))
        return SecXbrlResult(ok=True, filings=(filing,), facts=tuple(facts))


class Prices:
    license = ProviderLicense("fixture", "commercial_production", "fixture://terms")

    def __init__(self, days=5):
        self.days = days
        self.calls = []

    def daily_prices(self, security, start, end):
        self.calls.append(security.security_id)
        return [DailyPrice(security.security_id, start + timedelta(days=i), self.license.provider, D(40 if security.security_id == "A" else 20) + i, None, "USD", NOW, self.license.usage) for i in range(self.days)]


@pytest.fixture
def setup(tmp_path):
    return dict(connection=Database(), universe_provider=Universe(), filing_provider=Filings(), price_provider=Prices(),
                share_state=lambda listing, day, pit, price: {"shares_outstanding": D(1), "industry": "other", "revenue_comparable": True, "source": "fixture://reconciled-shares"},
                clock=lambda: NOW, run_id="run-10", checkpoint_dir=tmp_path, sensitivity_draws=8)


def run(setup, **kwargs):
    module = importlib.import_module("src.flows.us_country_index_flow")
    return module.run_us_country_index_flow(**(setup | kwargs))


def test_real_stages_publish_complete_manifest_and_schema_rows(setup):
    events = []
    result = run(setup, stage_hook=lambda stage: events.append(stage))
    assert result["status"] == "success", result
    assert events == STAGES
    assert list(result["stage_counts"]) == STAGES
    assert result["stage_counts"]["daily_calculations"] == 30
    assert result["publication_status"] == "published"
    assert result["previous_publication_preserved"] is False
    assert result["expected_keys"] == tuple(("us", metric, WEEK) for metric in ("pe", "pb", "ps", "pcf", "pfcf", "dividend_yield"))
    db = setup["connection"]
    assert db.publication == "run-10"
    assert db.events[-2:] == ["commit", "commit"]
    weekly = list(db.rows["core.country_weekly_metrics"].values())
    assert len(weekly) == 6
    assert all(row["daily_observation_count"] == 5 for row in weekly)
    assert all(row["source_coverage"]["sensitivity"]["interval_label"].startswith("experimental") for row in weekly)
    assert {row["metric_key"]: row["metric_value"] for row in weekly}["pe"] == D(86) / D(12)
    assert len(db.rows["raw.regulatory_facts"]) == 28


def test_checkpoint_reuse_after_failure_is_durable_and_audited(setup):
    def fail(stage):
        if stage == "weekly_summaries":
            raise RuntimeError("injected weekly failure")
    first = run(setup, stage_hook=fail)
    assert first["status"] == "failed"
    assert first["failed_stage"] == "weekly_summaries"
    assert first["previous_publication_preserved"] is True
    assert setup["connection"].publication == "previous-run"
    second = run(setup)
    assert second["status"] == "success", second
    assert second["reused_stages"] == STAGES[:5]
    assert setup["filing_provider"].calls == ["A", "B", "C", "D"]
    counts = {table: len(rows) for table, rows in setup["connection"].rows.items()}
    third = run(setup)
    assert third["reused_stages"] == STAGES
    assert {table: len(rows) for table, rows in setup["connection"].rows.items()} == counts


def test_one_nonmember_source_failure_is_structured_warning(setup):
    setup["filing_provider"].failed = {"D"}
    result = run(setup)
    assert result["status"] == "success", result
    assert result["source_errors"] == [{"provider": "sec", "key": "D", "external_series_id": "fixture://filing", "error_type": "fetch_error", "message": "exact source outage", "security_id": "D", "stage": "immutable_acquisition"}]
    assert result["source_warning_count"] == 1
    assert result["warning_count"] >= 1


@pytest.mark.parametrize("license", [ProviderLicense("yahoo_finance", "commercial_production"), ProviderLicense("fixture", "development_only"), ProviderLicense("fixture", "unapproved")])
def test_production_license_guard_preserves_previous_publication(setup, license):
    setup["price_provider"].license = license
    result = run(setup, environment="production")
    assert result["status"] == "failed"
    assert result["publication_status"] == "blocked_license"
    assert result["previous_publication_preserved"] is True
    assert setup["connection"].publication == "previous-run"


def test_fewer_than_three_days_publishes_unavailable_state_never_metric(setup):
    setup["price_provider"].days = 2
    result = run(setup)
    assert result["status"] == "success", result
    rows = list(setup["connection"].rows["core.country_weekly_metrics"].values())
    assert all(row["metric_value"] is None and row["metric_status"] == "unavailable" for row in rows)
    assert all(row["daily_observation_count"] == 2 for row in rows)


def test_atomic_pointer_failure_rolls_back_and_can_retry(setup):
    setup["connection"].fail_publish = True
    failed = run(setup)
    assert failed["status"] == "failed"
    assert "injected pointer failure" in failed["failure_summary"]
    assert setup["connection"].publication == "previous-run"
    assert not setup["connection"].rows.get("core.country_weekly_metrics")
    setup["connection"].fail_publish = False
    assert run(setup)["status"] == "success"


def test_missing_output_cannot_shrink_manifest(setup, monkeypatch):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    original = module.calculate_daily_country_metrics
    monkeypatch.setattr(module, "calculate_daily_country_metrics", lambda *a, **kw: [m for m in original(*a, **kw) if m.metric != "pfcf"])
    result = run(setup)
    assert result["status"] == "failed"
    assert "manifest" in result["failure_summary"]
    assert setup["connection"].publication == "previous-run"


def test_reusing_run_with_changed_configuration_is_rejected(setup):
    assert run(setup)["status"] == "success"
    result = run(setup, methodology_version="different")
    assert result["status"] == "failed"
    assert "checkpoint" in result["failure_summary"]


def test_missing_share_reconciliation_fails_without_silent_period_end_fallback(setup):
    result = run(setup, share_state=None)
    assert result["status"] == "failed"
    assert "shares" in result["failure_summary"]
    assert result["previous_publication_preserved"]


def test_hard_universe_failure_and_no_database_are_failed(setup):
    setup["universe_provider"].listings = []
    result = run(setup)
    assert result["status"] == "failed"
    assert result["previous_publication_preserved"]
    assert run(setup, connection=None)["status"] == "failed"
