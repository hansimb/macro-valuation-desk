from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal as D
import importlib
import json
import re

import pytest

from src.lib.pipeline.country_cohorts import CountryCohort
from src.lib.pipeline.uncertainty import AggregateContribution
from src.lib.source.adapters.sec_xbrl import SecXbrlResult
from src.lib.source.country_index_types import DailyPrice, FxRate, ProviderLicense, RawXbrlFact, RegulatoryFiling, SecurityListing


WEEK = date(2026, 9, 7)
NOW = datetime(2026, 9, 14, 8, tzinfo=UTC)
STAGES = ["immutable_acquisition", "normalization_point_in_time", "eligible_universe_prices_fx", "cohort_evaluation", "daily_calculations", "weekly_summaries", "sensitivity", "validation", "persistence_publication"]


class Database:
    """Transactional schema recorder; executes the real Task 9 writers and publisher."""
    def __init__(self):
        self.rows = {}
        self.publication = "previous-run"
        self.events = []
        self.table_events = []
        self.fail_publish = False
        self.tx_depth = 0

    @contextmanager
    def transaction(self):
        snapshot = deepcopy((self.rows, self.publication))
        outer = self.tx_depth == 0
        if outer:
            self.events.append("begin")
        self.tx_depth += 1
        try:
            yield
        except BaseException:
            self.rows, self.publication = snapshot
            if outer:
                self.events.append("rollback")
            raise
        else:
            if outer:
                self.events.append("commit")
        finally:
            self.tx_depth -= 1

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
        rows = list(rows)
        if rows:
            self.db.table_events.append((self.db.tx_depth, table, [dict(row) for row in rows]))
        for original in rows:
            row = dict(original)
            assert self.db.tx_depth > 0, "write would implicitly begin an uncommitted psycopg transaction"
            if table in {"core.country_daily_metrics", "core.country_weekly_metrics"}:
                assert self.db.rows["core.country_index_runs"][(row["run_id"],)]["run_status"] == "running"
            if table == "core.country_cohort_members":
                assert (row["primary_listing_id"],) in self.db.rows["core.primary_security_listings"]
            if table == "core.canonical_facts":
                assert (row["security_id"],) in self.db.rows["core.securities"]
            if table == "core.country_index_runs" and row["run_status"] == "completed":
                assert len(self.db.rows["core.country_weekly_metrics"]) == 6
            for key in ("source_coverage", "structured_reasons", "source_lineage", "content_json", "dimensions_json", "adjustment_metadata", "membership_reason", "structured_reason"):
                if key in row:
                    row[key] = json.loads(row[key])
            self.db.rows.setdefault(table, {})[tuple(row[k] for k in keys)] = row

    def execute(self, query, params=None):
        self.query = " ".join(query.split()).lower()
        self.params = params
        if self.query.startswith("insert into marts.country_index_publications"):
            if self.db.fail_publish:
                raise RuntimeError("injected pointer failure")
            self.db.publication = params["run_id"]
            self.db.events.append("publish")

    def fetchone(self):
        if "for update" in self.query and "core.country_index_runs" in self.query:
            return self.db.rows.get("core.country_index_runs", {}).get((self.params["run_id"],))
        return None

    def fetchall(self):
        if "from marts.country_index_publications" in self.query:
            return ([dict(market_id="us", metric_key=metric, week_id=WEEK)
                     for metric in ("pe", "pb", "ps", "pcf", "pfcf", "dividend_yield")]
                    if self.db.publication == self.params["run_id"] else [])
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
        return [DailyPrice(security.security_id, start + timedelta(days=i), self.license.provider, D(40 if security.security_id == "A" else 20) + i, None, security.trading_currency, NOW, self.license.usage) for i in range(self.days)]


class Fx:
    def __init__(self):
        self.calls = []

    def daily_rates(self, base_currency, quote_currency, start, end):
        self.calls.append((base_currency, quote_currency, start, end))
        return [FxRate(base_currency, quote_currency, start, D("1.10"), "fixture-fx", NOW, "fixture://fx")]


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
    assert db.events == ["begin", "publish", "commit"]
    tables = [table for _, table, _ in db.table_events]
    assert all(tx_depth == 1 for tx_depth, _, _ in db.table_events)
    assert tables.index("core.country_index_runs") < tables.index("core.country_daily_metrics")
    assert tables.index("core.primary_security_listings") < tables.index("core.country_cohort_members")
    weekly = list(db.rows["core.country_weekly_metrics"].values())
    assert len(weekly) == 6
    assert all(row["daily_observation_count"] == 5 for row in weekly)
    assert all(row["source_coverage"]["sensitivity"]["interval_label"].startswith("experimental") for row in weekly)
    assert {row["metric_key"]: row["metric_value"] for row in weekly}["pe"] == D(86) / D(12)
    assert len(db.rows["raw.regulatory_facts"]) == 28
    pit_rows = list(db.rows["core.point_in_time_fundamentals"].values())
    assert len(pit_rows) == 20
    assert all(len(row["source_lineage"]) == 7 for row in pit_rows)
    assert all(row["reporting_currency"] == "USD" for row in pit_rows)
    assert all(row["source_coverage"]["sensitivity"]["components"] for row in weekly)
    assert not any("missing_aggregate_contributions" in json.dumps(row["source_coverage"]) for row in weekly)
    assert sorted(path.suffix for path in setup["checkpoint_dir"].iterdir()) == [".json"] * len(STAGES)


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
    assert second["source_errors"] == []
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
    second = run(setup)
    assert second["reused_stages"] == STAGES
    assert second["source_errors"] == result["source_errors"]


def test_member_source_failure_fails_after_cohort_selection(setup):
    setup["filing_provider"].failed = {"A"}
    result = run(setup)
    assert result["status"] == "failed"
    assert result["failed_stage"] == "validation"
    assert "cohort member" in result["failure_summary"]
    assert setup["connection"].publication == "previous-run"


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
    assert setup["connection"].rows == {}
    assert not (setup["checkpoint_dir"] / "run-10.persistence_publication.json").exists()
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


def test_corrupt_checkpoint_json_fails_closed(setup):
    assert run(setup)["status"] == "success"
    (setup["checkpoint_dir"] / "run-10.immutable_acquisition.json").write_text("{bad", encoding="utf-8")
    result = run(setup)
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


def test_non_usd_prices_request_base_currency_to_usd_fx(setup):
    setup["universe_provider"].listings = [
        SecurityListing("l-A", "A", "A", "A", "common_stock", "us", "XNAS", "A", "USD", date(2020, 1, 1), "active", "fixture", "A"),
        SecurityListing("l-B", "B", "B", "B", "common_stock", "us", "XNAS", "B", "EUR", date(2020, 1, 1), "active", "fixture", "B"),
        SecurityListing("l-C", "C", "C", "C", "common_stock", "us", "XNAS", "C", "USD", date(2020, 1, 1), "active", "fixture", "C"),
        SecurityListing("l-D", "D", "D", "D", "common_stock", "us", "XNAS", "D", "USD", date(2020, 1, 1), "active", "fixture", "D"),
    ]
    fx = Fx()
    result = run(setup, fx_provider=fx)
    assert result["status"] == "success", result
    assert fx.calls == [("EUR", "USD", WEEK + timedelta(days=index), WEEK + timedelta(days=index)) for index in range(5)]


def test_active_cohort_state_is_reused_with_formation_weights(setup):
    active = CountryCohort("us", date(2026, 1, 5), ("A", "B", "C"), 3, D("0.80"))
    result = run(setup, cohort_state=lambda **_: {"cohort": active, "formation_caps": {"A": D(40), "B": D(20), "C": D(20)}, "evaluated_week": WEEK - timedelta(days=7)})
    assert result["status"] == "success", result
    assert set(setup["connection"].rows["core.country_cohorts"]) == {("us", "2026-01-05")}
    weights = {
        row["security_id"]: row["market_weight_at_formation"]
        for row in setup["connection"].rows["core.country_cohort_members"].values()
    }
    assert weights == {"A": D("0.5"), "B": D("0.25"), "C": D("0.25")}


def test_no_argument_flow_fails_structurally_before_opening_database(monkeypatch):
    module = importlib.import_module("src.flows.us_country_index_flow")
    monkeypatch.setattr(module, "load_project_env", lambda: None)
    monkeypatch.delenv("MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY", raising=False)
    monkeypatch.setattr(module, "get_connection", lambda: pytest.fail("unconfigured providers must be detected first"))
    result = module.run_us_country_index_flow()
    assert result["status"] == "failed"
    assert result["failed_stage"] == "configuration"
    assert "MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY" in result["failure_summary"]
    assert module.main(lambda: result) == 1


def test_environment_provider_factory_runs_configured_task(setup, monkeypatch):
    module = importlib.import_module("src.flows.us_country_index_flow")
    monkeypatch.setattr(module, "load_project_env", lambda: None)
    monkeypatch.setattr(module, "fixture_factory", lambda: setup, raising=False)
    monkeypatch.setenv("MVD_US_COUNTRY_INDEX_PROVIDER_FACTORY", "src.flows.us_country_index_flow:fixture_factory")
    assert module.run_us_country_index_flow()["status"] == "success"


@pytest.mark.parametrize("change", ["terms", "usage", "version", "price_config", "private_config", "fx", "shares"])
def test_checkpoint_fingerprint_invalidates_source_and_method_configuration(setup, change):
    assert run(setup)["status"] == "success"
    extra = {}
    prices = setup["price_provider"]
    if change == "terms":
        prices.license = replace(prices.license, terms_url="fixture://new-terms")
    elif change == "usage":
        prices.license = replace(prices.license, usage="development_only")
    elif change == "version":
        prices.version = "v2"
    elif change == "price_config":
        prices.days = 4
    elif change == "private_config":
        prices._endpoint = "fixture://new-endpoint"
    elif change == "fx":
        extra["fx_provider"] = Fx()
    else:
        extra["share_state"] = lambda *args: {"shares_outstanding": D(2), "source": "fixture://different"}
    result = run(setup, **extra)
    assert result["status"] == "failed"
    assert result["failed_stage"] == "checkpoint"
    assert setup["connection"].events.count("commit") == 1


def test_checkpoint_checksum_and_type_are_validated_before_reuse(setup):
    assert run(setup)["status"] == "success"
    path = setup["checkpoint_dir"] / "run-10.immutable_acquisition.json"
    envelope = json.loads(path.read_text())
    assert envelope["version"] == 3
    envelope["payload"] = {"type": "os.system", "fields": {}}
    path.write_text(json.dumps(envelope))
    result = run(setup)
    assert result["status"] == "failed"
    assert "checkpoint" in result["failure_summary"]


def test_persistence_checkpoint_is_written_only_after_outer_commit(setup, monkeypatch):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    original = module._write_checkpoint
    def checked(path, fingerprint, name, value):
        if name == "persistence_publication":
            assert setup["connection"].tx_depth == 0
            assert setup["connection"].events[-1] == "commit"
        else:
            assert not setup["connection"].rows
        original(path, fingerprint, name, value)
    monkeypatch.setattr(module, "_write_checkpoint", checked)
    assert run(setup)["status"] == "success"


def test_existing_psycopg_transaction_cannot_be_mistaken_for_durable_commit(setup):
    from types import SimpleNamespace
    setup["connection"].info = SimpleNamespace(transaction_status=2)
    result = run(setup)
    assert result["status"] == "failed"
    assert "idle" in result["failure_summary"]
    assert not setup["connection"].events


def test_reconciled_fx_lineage_is_persisted_and_reporting_currency_is_used(setup):
    original = setup["filing_provider"].fetch_companyfacts
    def euro_facts(sid):
        result = original(sid)
        return replace(result, facts=tuple(replace(f, unit="EUR") if f.unit == "USD" else f for f in result.facts))
    setup["filing_provider"].fetch_companyfacts = euro_facts
    fx = Fx()
    result = run(setup, fx_provider=fx)
    assert result["status"] == "success", result
    assert len(fx.calls) == 5
    coverage = next(iter(setup["connection"].rows["core.country_index_runs"].values()))["source_coverage"]
    assert len(coverage["fx_rates"]) == 5
    assert {r["base_currency"] for r in coverage["fx_rates"]} == {"EUR"}
    assert all(r["source_url"] == "fixture://fx" for r in coverage["fx_rates"])
    assert all(row["reporting_currency"] == "EUR" for row in setup["connection"].rows["core.point_in_time_fundamentals"].values())


def test_fx_rejects_wrong_date_and_missing_lineage(setup):
    setup["universe_provider"].listings[1] = replace(setup["universe_provider"].listings[1], trading_currency="EUR")
    fx = Fx()
    fx.daily_rates = lambda base, quote, start, end: [FxRate(base, quote, start-timedelta(days=1), D(1), "fixture", NOW)]
    result = run(setup, fx_provider=fx)
    assert result["status"] == "failed"
    assert "FX rate" in result["failure_summary"]


def test_sensitivity_uses_fixed_cohort_aggregate_contributions_and_supplied_staleness(setup, monkeypatch):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    original = module.estimate_sensitivity
    captured = []
    def estimate(value, cohort, **kwargs):
        captured.append(value)
        return original(value, cohort, **kwargs)
    monkeypatch.setattr(module, "estimate_sensitivity", estimate)
    result = run(setup, sensitivity_context=lambda **_: {"staleness_changes": {"A": D("0.1")}, "peer_contributions": {}})
    assert result["status"] == "success", result
    pe = next(value for value in captured if value.metric.metric == "pe" and value.metric.valuation_date == WEEK + timedelta(days=2))
    assert set(pe.contributions) == {"A", "B", "C"}
    assert pe.contributions["A"].numerator == D(42)
    assert pe.contributions["A"].denominator == D(4)
    assert pe.staleness_changes == {"A": D("0.1")}
    row = next(r for r in setup["connection"].rows["core.country_weekly_metrics"].values() if r["metric_key"] == "pe")
    assert row["interval_lower"] < row["interval_upper"]
    assert any(c["code"] == "staleness" and c["available"] for c in row["source_coverage"]["sensitivity"]["components"])


def test_degenerate_sensitivity_result_cannot_publish(setup, monkeypatch):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    original = module.estimate_sensitivity
    monkeypatch.setattr(module, "estimate_sensitivity", lambda value, cohort, **kwargs: original(value.metric, cohort, **kwargs))
    result = run(setup)
    assert result["status"] == "failed"
    assert "aggregate contribution" in result["failure_summary"]
    assert not setup["connection"].rows


@pytest.mark.parametrize("prior_weeks,previous_offset,expected_date,reason", [(0, 7, date(2026, 1, 5), None), (1, 7, WEEK, "exceptional_reconstitution"), (1, 14, date(2026, 1, 5), None)])
def test_cohort_reconstitution_requires_two_consecutive_weekly_breaches(setup, prior_weeks, previous_offset, expected_date, reason):
    active = CountryCohort("us", date(2026, 1, 5), ("B", "C", "D"), 3, D("0.8"), consecutive_outside_tolerance_weeks=prior_weeks)
    prior = {"cohort": active, "formation_caps": {"B": D(50), "C": D(15), "D": D(15)}, "evaluated_week": WEEK-timedelta(days=previous_offset)}
    result = run(setup, cohort_state=prior)
    assert result["status"] == "success", result
    state = result["next_cohort_state"]
    assert state["cohort"].effective_date == expected_date
    if reason:
        assert reason in state["cohort"].reasons
    else:
        assert state["cohort"].security_ids == ("B", "C", "D")
        assert state["formation_caps"] == prior["formation_caps"]
        weight = setup["connection"].rows["core.country_cohort_members"][("us", "2026-01-05", "B")]["market_weight_at_formation"]
        assert weight == D("0.625")


@pytest.mark.parametrize("forced", [False, True])
def test_annual_or_explicit_forced_reconstitution(setup, forced):
    active = CountryCohort("us", date(2025 if not forced else 2026, 1, 5), ("A", "B", "C"), 3, D("0.8"))
    state = {"cohort": active, "formation_caps": {"A": D(40), "B": D(20), "C": D(20)}, "evaluated_week": WEEK-timedelta(days=7)}
    if forced:
        state["forced_replacements"] = {"C": "D"}
    result = run(setup, cohort_state=state)
    assert result["status"] == "success", result
    cohort = result["next_cohort_state"]["cohort"]
    assert cohort.effective_date == WEEK
    assert ("forced_replacement" if forced else "annual_reconstitution") in cohort.reasons
    if forced:
        assert set(cohort.security_ids) == {"A", "B", "D"}
        assert cohort.constituent_target_count == 3


def test_price_dates_cannot_escape_monday_friday_window(setup):
    setup["price_provider"].days = 6
    result = run(setup)
    assert result["status"] == "failed"
    assert "Monday-Friday" in result["failure_summary"]


def test_state_fingerprint_tracks_injected_cohort_formation_configuration(setup):
    active = CountryCohort("us", date(2026, 1, 5), ("A", "B", "C"), 3, D("0.8"))
    state = {"cohort": active, "formation_caps": {"A": D(40), "B": D(20), "C": D(20)}, "evaluated_week": WEEK-timedelta(days=7)}
    assert run(setup, cohort_state=state)["status"] == "success"
    state["formation_caps"]["A"] = D(50)
    result = run(setup, cohort_state=state)
    assert result["status"] == "failed"
    assert result["failed_stage"] == "checkpoint"


def test_four_day_sensitivity_point_matches_weekly_median(setup):
    setup["price_provider"].days = 4
    result = run(setup)
    assert result["status"] == "success", result
    rows = setup["connection"].rows["core.country_weekly_metrics"].values()
    assert all(abs(D(row["source_coverage"]["sensitivity"]["point_estimate"])-row["metric_value"]) < D("1e-25") for row in rows)


def test_atomic_replace_failure_leaves_no_completed_stage_checkpoint(setup, monkeypatch):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    def fail_replace(*args):
        raise OSError("injected checkpoint replace failure")
    monkeypatch.setattr(module.os, "replace", fail_replace)
    result = run(setup)
    assert result["status"] == "failed"
    assert not list(setup["checkpoint_dir"].iterdir())
    assert not setup["connection"].rows


def _remove_a_earnings(setup):
    original = setup["filing_provider"].fetch_companyfacts
    def missing(sid):
        result = original(sid)
        return replace(result, facts=tuple(f for f in result.facts if sid != "A" or f.concept_name != "NetIncomeLossAvailableToCommonStockholdersBasic"))
    setup["filing_provider"].fetch_companyfacts = missing


def test_missing_fixed_constituent_is_imputed_before_weekly_summary(setup):
    _remove_a_earnings(setup)
    def peers(**kwargs):
        row = kwargs["metric"]
        if row.metric != "pe":
            return {}
        cap = D(40 + (row.valuation_date-WEEK).days)
        return {"peer_contributions": {"A": (AggregateContribution(cap, D(2)), AggregateContribution(cap, D(4)), AggregateContribution(cap, D(6)))}}
    result = run(setup, sensitivity_context=peers)
    assert result["status"] == "success", result
    weekly = setup["connection"].rows["core.country_weekly_metrics"][("run-10", "us", "pe", WEEK)]
    assert weekly["metric_status"] == "warning"
    assert weekly["metric_value"] == D(86)/D(12)
    assert weekly["daily_observation_count"] == 5
    assert weekly["actual_constituent_count"] == 3
    assert weekly["interval_lower"] < weekly["metric_value"] < weekly["interval_upper"]
    assert "partly_estimated" in weekly["structured_reasons"]
    assert "missing_fact" in weekly["structured_reasons"]
    monday = setup["connection"].rows["core.country_daily_metrics"][("run-10", "us", "pe", WEEK)]
    assert monday["imputed_coverage"] == D("0.5")
    assert monday["reported_fact_coverage"] == D("0.5")
    assert monday["carried_forward_coverage"] == D(0)
    assert monday["missing_or_invalid_coverage"] == D(0)
    assert "experimental" in monday["source_coverage"]["sensitivity"]["interval_label"]


def test_missing_peers_remain_explicitly_unavailable(setup):
    _remove_a_earnings(setup)
    result = run(setup)
    assert result["status"] == "success", result
    weekly = setup["connection"].rows["core.country_weekly_metrics"][("run-10", "us", "pe", WEEK)]
    assert weekly["metric_status"] == "unavailable"
    assert weekly["metric_value"] is None
    assert "missing_peer_contributions" in weekly["structured_reasons"]
    assert weekly["imputed_coverage"] in (None, D(0))


@pytest.mark.parametrize("invalid", ["unavailable", "nan", "null_interval", "negative_draw"])
def test_unusable_sensitivity_never_leaves_available_headline(setup, monkeypatch, invalid):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    original = module.estimate_sensitivity
    def broken(value, cohort, **kwargs):
        result = original(value, cohort, **kwargs)
        if value.metric.metric != "pe":
            return result
        if invalid == "unavailable":
            return replace(result, status="unavailable", point_estimate=None, lower=None, upper=None, reason="non_positive_denominator_in_sensitivity_draw")
        if invalid == "nan":
            return replace(result, upper=D("NaN"))
        if invalid == "null_interval":
            return replace(result, lower=None)
        return replace(result, draw_values=(D(-1), *result.draw_values[1:]))
    monkeypatch.setattr(module, "estimate_sensitivity", broken)
    result = run(setup)
    assert result["status"] == "success", result
    weekly = setup["connection"].rows["core.country_weekly_metrics"][("run-10", "us", "pe", WEEK)]
    assert weekly["metric_status"] == "unavailable"
    assert weekly["metric_value"] is None
    assert weekly["interval_lower"] is None and weekly["interval_upper"] is None
    assert any("sensitivity" in reason for reason in weekly["structured_reasons"])
    assert all(r["metric_value"] is None for r in setup["connection"].rows["core.country_daily_metrics"].values() if r["metric_key"] == "pe")


def test_sensitivity_warnings_persist_with_metadata_and_deduplicated_counts(setup, monkeypatch):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    original = module.estimate_sensitivity
    def duplicates(value, cohort, **kwargs):
        result = original(value, cohort, **kwargs)
        return replace(result, warnings=(*result.warnings, *result.warnings))
    monkeypatch.setattr(module, "estimate_sensitivity", duplicates)
    result = run(setup, sensitivity_context=lambda **_: {"staleness_changes": {"A": D("0.1")}})
    assert result["status"] == "success", result
    rows = setup["connection"].rows["core.country_weekly_metrics"].values()
    assert all("staleness" in row["structured_reasons"] and "concentration" in row["structured_reasons"] for row in rows)
    assert all(len(row["structured_reasons"]) == len(set(row["structured_reasons"])) for row in rows)
    warnings = setup["connection"].rows["core.country_metric_warnings"].values()
    assert len(warnings) == result["warning_count"]
    stale = next(row for row in warnings if row["metric_key"] == "pe" and row["warning_code"] == "staleness")
    assert stale["interval_width_contribution"] > 0
    assert stale["affected_market_weight"] > 0
    assert stale["warning_level"] == "experimental"
    assert stale["structured_reason"]["component"]["code"] == "staleness"


@pytest.mark.parametrize("superseded", [False, True])
def test_post_commit_checkpoint_failure_recovers_without_republishing(setup, monkeypatch, superseded):
    module = importlib.import_module("src.tasks.run_us_country_index_etl")
    original = module.os.replace
    def fail_publication_checkpoint(source, target):
        if str(target).endswith("persistence_publication.json"):
            raise OSError("injected post-commit checkpoint failure")
        original(source, target)
    monkeypatch.setattr(module.os, "replace", fail_publication_checkpoint)
    first = run(setup)
    assert first["status"] == "failed"
    assert first["publication_status"] == "published"
    assert setup["connection"].events.count("publish") == 1
    assert first["warning_count"] == len(setup["connection"].rows["core.country_metric_warnings"])
    monkeypatch.setattr(module.os, "replace", original)
    if superseded:
        setup["connection"].publication = "newer-run"
    second = run(setup)
    assert setup["connection"].events.count("publish") == 1
    assert setup["filing_provider"].calls == ["A", "B", "C", "D"]
    if superseded:
        assert second["status"] == "failed"
        assert "current" in second["failure_summary"]
        assert setup["connection"].publication == "newer-run"
    else:
        assert second["status"] == "success", second
        assert "persistence_publication" in second["reused_stages"]
        assert (setup["checkpoint_dir"] / "run-10.persistence_publication.json").exists()


def test_real_nonpositive_sensitivity_draw_is_unavailable_with_engine_warning(setup):
    result = run(setup, sensitivity_context=lambda **_: {"staleness_changes": {"A": D(4)}})
    assert result["status"] == "success", result
    weekly = setup["connection"].rows["core.country_weekly_metrics"][("run-10", "us", "pe", WEEK)]
    assert weekly["metric_status"] == "unavailable"
    assert weekly["metric_value"] is None
    assert "non_positive_denominator" in weekly["structured_reasons"]
    warning = setup["connection"].rows["core.country_metric_warnings"][("run-10", "us", "pe", WEEK, "non_positive_denominator")]
    assert warning["structured_reason"]["component"]["available"] is True
    monday = setup["connection"].rows["core.country_daily_metrics"][("run-10", "us", "pe", WEEK)]
    assert monday["source_coverage"]["sensitivity"]["reason"] == "non_positive_denominator_in_sensitivity_draw"


def test_completed_checkpoint_cannot_republish_superseded_run(setup):
    assert run(setup)["status"] == "success"
    setup["connection"].publication = "newer-run"
    result = run(setup)
    assert result["status"] == "failed"
    assert "not current" in result["failure_summary"]
    assert setup["connection"].events.count("publish") == 1


def test_imputation_cannot_replace_observed_market_cap(setup):
    _remove_a_earnings(setup)
    def peers(**kwargs):
        if kwargs["metric"].metric == "pe":
            return {"peer_contributions": {"A": (AggregateContribution(D(999), D(4)),)}}
        return {}
    result = run(setup, sensitivity_context=peers)
    assert result["status"] == "failed"
    assert "observed market cap" in result["failure_summary"]
    assert not setup["connection"].rows
