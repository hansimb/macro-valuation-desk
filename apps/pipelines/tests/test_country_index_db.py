from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, date, datetime
from decimal import Decimal
import json

import pytest

from src.lib.db.country_indices import (
    CountryIndexContractError,
    PublicationInvariantError,
    publish_completed_run,
    upsert_country_daily_metrics,
    upsert_regulatory_filings,
    upsert_regulatory_facts,
    upsert_security_prices,
)


class RecordingCursor:
    def __init__(self, connection: "RecordingConnection") -> None:
        self.connection = connection

    def execute(self, query: str, params: object | None = None) -> None:
        self.connection.commands.append(("execute", " ".join(query.split()), params))
        self.connection._last_query = query

    def executemany(self, query: str, params_seq: object) -> None:
        self.connection.commands.append(("executemany", " ".join(query.split()), list(params_seq)))

    def fetchone(self):
        return self.connection.fetchone_results.pop(0) if self.connection.fetchone_results else None

    def fetchall(self):
        return self.connection.fetchall_results.pop(0) if self.connection.fetchall_results else []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class RecordingConnection:
    def __init__(self, *, fetchone_results=(), fetchall_results=()) -> None:
        self.commands: list[tuple[str, str, object | None]] = []
        self.fetchone_results = list(fetchone_results)
        self.fetchall_results = list(fetchall_results)
        self.events: list[str] = []
        self._last_query = ""

    def cursor(self) -> RecordingCursor:
        return RecordingCursor(self)

    @contextmanager
    def transaction(self):
        self.events.append("begin")
        try:
            yield self
        except BaseException:
            self.events.append("rollback")
            raise
        else:
            self.events.append("commit")


def _commands(connection: RecordingConnection) -> str:
    return "\n".join(query for _, query, _ in connection.commands).lower()


def _completed_run() -> dict[str, object]:
    return {
        "run_id": "run-2026-06-08",
        "methodology_version": "mvd-v1",
        "run_status": "completed",
        "completed_at": datetime(2026, 6, 8, 6, tzinfo=UTC),
    }


def _valid_weekly_row() -> dict[str, object]:
    return {
        "market_id": "us",
        "metric_key": "pe",
        "week_id": date(2026, 6, 1),
        "cohort_version": "us-2026-v1",
        "methodology_version": "mvd-v1",
        "metric_value": Decimal("20.1"),
        "weekly_min_value": Decimal("19.8"),
        "weekly_max_value": Decimal("20.4"),
        "valuation_dates": [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)],
        "daily_observation_count": 3,
        "metric_status": "warning",
        "market_coverage": Decimal("0.77"),
        "reported_fact_coverage": Decimal("0.65"),
        "carried_forward_coverage": Decimal("0.10"),
        "imputed_coverage": Decimal("0.02"),
        "missing_or_invalid_coverage": Decimal("0.23"),
        "metric_eligible_coverage": Decimal("0.80"),
        "actual_constituent_count": 100,
        "cohort_target_count": 100,
        "effective_constituent_count": Decimal("45.3"),
        "largest_constituent_weight": Decimal("0.08"),
        "top_five_concentration": Decimal("0.24"),
        "top_ten_concentration": Decimal("0.37"),
        "membership_overlap": Decimal("1"),
        "interval_lower": Decimal("18.9"),
        "interval_upper": Decimal("21.4"),
        "source_coverage": {"reported": "0.65", "carried_forward": "0.10"},
        "structured_reasons": [{"code": "holiday_or_missing_trading_day"}],
    }


def _daily_rows(
    values: tuple[Decimal | None, ...] = (Decimal("19.8"), Decimal("20.1"), Decimal("20.4")),
    statuses: tuple[str, ...] | None = None,
) -> list[dict[str, object]]:
    resolved_statuses = statuses or tuple("warning" for _ in values)
    return [
        {
            "market_id": "us",
            "metric_key": "pe",
            "valuation_date": date(2026, 6, day),
            "metric_value": value,
            "metric_status": status,
            "structured_reasons": [{"code": "non_positive_denominator"}] if status == "unavailable" else [],
        }
        for day, value, status in zip(range(1, len(values) + 1), values, resolved_statuses, strict=True)
    ]


EXPECTED_PE = (("us", "pe", date(2026, 6, 1)),)


def test_raw_rows_are_parameterized_and_immutable() -> None:
    connection = RecordingConnection()
    injected = "sec'; drop table raw.regulatory_filings; --"
    fetched_at = datetime(2026, 6, 8, 1, tzinfo=UTC)

    upsert_regulatory_filings(connection, [{
        "provider": injected,
        "external_id": "0001",
        "content_hash": "sha256:one",
        "jurisdiction": "US",
        "filer_id": "0000320193",
        "filing_form": "10-Q",
        "filing_date": date(2026, 5, 1),
        "accepted_at": fetched_at,
        "published_at": fetched_at,
        "amendment_of_external_id": None,
        "document_url": "https://example.test/filing",
        "content_json": {"nested": {"amount": Decimal("1.20")}},
        "fetched_at": fetched_at,
    }])
    upsert_regulatory_facts(connection, [{
        "filing_provider": injected,
        "filing_external_id": "0001",
        "filing_content_hash": "sha256:one",
        "fact_id": "fact-1",
        "entity_id": "issuer-1",
        "security_id": "security-1",
        "taxonomy": "us-gaap",
        "concept_name": "Revenues",
        "context_id": "ctx",
        "dimensions_json": {"segment": "all"},
        "unit": "USD",
        "decimals": "-6",
        "value_text": "1200000",
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 3, 31),
        "instant_date": None,
        "is_consolidated": True,
        "is_continuing_operations": True,
    }])
    upsert_security_prices(connection, [{
        "security_id": "security-1",
        "trading_date": date(2026, 6, 5),
        "provider": "prices",
        "close_price": Decimal("123.45"),
        "split_adjusted_close_price": Decimal("120"),
        "trading_currency": "USD",
        "adjustment_metadata": {"split": [4, 1]},
        "provider_timestamp": fetched_at,
        "license_class": "development_only",
        "source_url": "https://example.test/price",
    }])

    sql = _commands(connection)
    assert sql.count("on conflict") == 3
    assert sql.count("do nothing") == 3
    assert injected not in sql
    params = [params for _, _, params in connection.commands]
    assert any(injected in row.values() for rows in params if isinstance(rows, list) for row in rows)
    filing_params = params[0][0]
    assert json.loads(filing_params["content_json"])["nested"]["amount"] == "1.20"
    assert params[2][0]["close_price"] == Decimal("123.45")
    assert params[2][0]["provider_timestamp"] == fetched_at


def test_derived_daily_rows_only_update_the_same_run_methodology_and_cohort() -> None:
    connection = RecordingConnection()
    row = _valid_weekly_row()
    daily = {
        key: row[key]
        for key in (
            "market_id", "metric_key", "cohort_version", "methodology_version", "metric_value",
            "metric_status", "market_coverage", "reported_fact_coverage", "carried_forward_coverage",
            "imputed_coverage", "missing_or_invalid_coverage", "metric_eligible_coverage",
            "actual_constituent_count", "cohort_target_count", "effective_constituent_count",
            "largest_constituent_weight", "top_five_concentration", "top_ten_concentration",
            "membership_overlap", "interval_lower", "interval_upper", "source_coverage", "structured_reasons",
        )
    }
    daily.update({"run_id": "run-2026-06-08", "valuation_date": date(2026, 6, 3), "value_currency": "USD"})

    upsert_country_daily_metrics(connection, [daily])

    sql = _commands(connection)
    assert "on conflict (run_id, market_id, metric_key, valuation_date) do update" in sql
    assert "where core.country_daily_metrics.methodology_version = excluded.methodology_version" in sql
    assert "and core.country_daily_metrics.cohort_version = excluded.cohort_version" in sql
    assert "delete from" not in sql
    params = connection.commands[0][2][0]
    assert params["interval_lower"] == Decimal("18.9")
    assert json.loads(params["structured_reasons"])[0]["code"] == "holiday_or_missing_trading_day"


def test_failed_or_partial_run_rolls_back_before_replacing_prior_publication() -> None:
    connection = RecordingConnection(fetchone_results=[{
        **_completed_run(), "run_status": "failed",
    }])

    with pytest.raises(PublicationInvariantError, match="completed"):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=EXPECTED_PE)

    assert connection.events == ["begin", "rollback"]
    assert "update marts.country_index_publications" not in _commands(connection)
    assert "insert into marts.country_index_publications" not in _commands(connection)


def test_publication_rejects_a_manifest_key_missing_from_both_daily_and_weekly_outputs() -> None:
    expected = (*EXPECTED_PE, ("us", "pb", date(2026, 6, 1)))
    connection = RecordingConnection(
        fetchone_results=[_completed_run()],
        fetchall_results=[_daily_rows(), [_valid_weekly_row()]],
    )

    with pytest.raises(PublicationInvariantError, match="daily key set"):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=expected)

    assert connection.events == ["begin", "rollback"]
    assert "update marts.country_index_publications" not in _commands(connection)


def test_publication_rejects_an_extra_weekly_output_not_in_the_manifest() -> None:
    extra = {**_valid_weekly_row(), "metric_key": "pb"}
    connection = RecordingConnection(
        fetchone_results=[_completed_run()],
        fetchall_results=[_daily_rows(), [_valid_weekly_row(), extra]],
    )

    with pytest.raises(PublicationInvariantError, match="weekly key set"):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=EXPECTED_PE)

    assert connection.events == ["begin", "rollback"]
    assert "update marts.country_index_publications" not in _commands(connection)


def test_publication_recomputes_exact_even_day_median_and_daily_bounds() -> None:
    weekly = _valid_weekly_row()
    weekly.update({
        "metric_value": Decimal("20"),
        "weekly_min_value": Decimal("10"),
        "weekly_max_value": Decimal("40"),
        "valuation_dates": [date(2026, 6, day) for day in (1, 2, 3, 4)],
        "daily_observation_count": 4,
    })
    connection = RecordingConnection(
        fetchone_results=[_completed_run()],
        fetchall_results=[_daily_rows((Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40"))), [weekly]],
    )

    with pytest.raises(PublicationInvariantError, match="daily median"):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=EXPECTED_PE)

    assert connection.events == ["begin", "rollback"]
    assert "update marts.country_index_publications" not in _commands(connection)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"valuation_dates": [date(2026, 6, 1), date(2026, 6, 3), date(2026, 6, 2)]}, "dates or count"),
        ({"daily_observation_count": 2}, "dates or count"),
        ({"weekly_min_value": Decimal("19.9")}, "range"),
    ],
)
def test_publication_rejects_fabricated_weekly_dates_count_or_range(change: dict[str, object], message: str) -> None:
    weekly = {**_valid_weekly_row(), **change}
    connection = RecordingConnection(
        fetchone_results=[_completed_run()],
        fetchall_results=[_daily_rows(), [weekly]],
    )

    with pytest.raises(PublicationInvariantError, match=message):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=EXPECTED_PE)

    assert connection.events == ["begin", "rollback"]
    assert "update marts.country_index_publications" not in _commands(connection)


def test_publication_rejects_unavailable_week_with_three_valid_daily_values() -> None:
    weekly = _valid_weekly_row()
    weekly.update({"metric_status": "unavailable", "metric_value": None})
    connection = RecordingConnection(
        fetchone_results=[_completed_run()],
        fetchall_results=[_daily_rows(), [weekly]],
    )

    with pytest.raises(PublicationInvariantError, match="unavailable"):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=EXPECTED_PE)

    assert connection.events == ["begin", "rollback"]


def test_publication_rejects_empty_or_duplicate_expected_manifest_without_touching_database() -> None:
    connection = RecordingConnection()

    with pytest.raises(CountryIndexContractError, match="must not be empty"):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=[])
    with pytest.raises(CountryIndexContractError, match="must be unique"):
        publish_completed_run(connection, "run-2026-06-08", expected_keys=[*EXPECTED_PE, *EXPECTED_PE])

    assert connection.commands == []
    assert connection.events == []


def test_completed_run_atomically_replaces_current_pointer_and_is_idempotent() -> None:
    weekly = _valid_weekly_row()
    connection = RecordingConnection(
        fetchone_results=[_completed_run(), _completed_run()],
        fetchall_results=[
            _daily_rows(), [weekly],
            _daily_rows(), [weekly],
        ],
    )

    publish_completed_run(connection, "run-2026-06-08", expected_keys=EXPECTED_PE)
    publish_completed_run(connection, "run-2026-06-08", expected_keys=EXPECTED_PE)

    sql = _commands(connection)
    assert connection.events == ["begin", "commit", "begin", "commit"]
    assert "pg_advisory_xact_lock" in sql
    assert "for update" in sql
    assert sql.index("from core.country_daily_metrics") < sql.index("update marts.country_index_publications")
    assert "from core.country_daily_metrics" in sql and "for update" in sql
    assert sql.index("update marts.country_index_publications") < sql.index("insert into marts.country_index_publications")
    assert "delete from marts.country_index_publications" not in sql
    assert "on conflict (run_id, market_id, metric_key, week_id) do update" in sql
    assert "where publication.is_current" in sql
    assert all("run-2026-06-08" not in query for _, query, _ in connection.commands)
    assert any(params == {"run_id": "run-2026-06-08"} for _, _, params in connection.commands)
