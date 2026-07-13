from __future__ import annotations

from prefect import task

from src.lib.db.equity_market_valuation import (
    replace_equity_market_valuation_snapshots,
    upsert_equity_market_valuation_payloads,
)
from src.lib.pipeline.checkpoints import utc_now_iso
from src.lib.pipeline.equity_market_universe import EQUITY_MARKET_UNIVERSE, MarketDefinition
from src.lib.pipeline.transforms.equity_market_valuation import to_equity_market_valuation_row
from src.lib.source.adapters.eodhd import EodhdAdapter


def _adapter_for_provider(provider: str, adapter_factories=None):
    if adapter_factories and provider in adapter_factories:
        return adapter_factories[provider]()

    if provider == "eodhd":
        return EodhdAdapter()

    raise ValueError(f"Unsupported equity market valuation provider: {provider}")


def _failure_summary(
    *,
    market_count: int,
    error_count: int,
    mart_rows: int,
    raw_payload_rows: int,
    errors: list[str],
) -> str | None:
    if not errors:
        return None

    if error_count == market_count:
        scope = f"all {market_count} markets"
    else:
        scope = f"{error_count} of {market_count} markets"
    return (
        f"Equity market valuation ETL failed for {scope}; wrote {mart_rows} mart rows and "
        f"{raw_payload_rows} raw payload rows. First error: {errors[0]}"
    )


@task
def run_equity_market_valuation_etl(
    connection=None,
    *,
    definitions: list[MarketDefinition] | None = None,
    adapter_factories=None,
) -> dict[str, object]:
    universe = definitions or EQUITY_MARKET_UNIVERSE
    adapters = {}
    fetched_at = utc_now_iso()
    payload_rows: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []
    errors: list[str] = []

    for definition in universe:
        adapter = adapters.setdefault(
            definition.provider,
            _adapter_for_provider(definition.provider, adapter_factories),
        )
        result = adapter.fetch_fundamentals_snapshot(definition.measured_symbol)
        if not result.ok or result.snapshot is None:
            message = result.error.message if result.error is not None else "provider fetch failed"
            errors.append(f"{definition.market_id}: {message}")
            continue

        if result.payload_json is not None:
            payload_rows.append(
                {
                    "provider": result.snapshot.provider,
                    "external_symbol": definition.measured_symbol,
                    "fetched_at": fetched_at,
                    "payload_json": result.payload_json,
                }
            )
        rows.append(to_equity_market_valuation_row(result.snapshot, definition))

    try:
        if payload_rows:
            upsert_equity_market_valuation_payloads(connection, payload_rows)
        if rows:
            replace_equity_market_valuation_snapshots(connection, rows)
        if connection is not None and (payload_rows or rows):
            connection.commit()
    except Exception:
        if connection is not None:
            connection.rollback()
        raise

    result = {
        "status": "failed" if errors else "success",
        "mart_rows": len(rows),
        "raw_payload_rows": len(payload_rows),
        "fetched_at": fetched_at,
        "errors": errors,
    }

    summary = _failure_summary(
        market_count=len(universe),
        error_count=len(errors),
        mart_rows=len(rows),
        raw_payload_rows=len(payload_rows),
        errors=errors,
    )
    if summary is not None:
        result["failure_summary"] = summary

    return result
