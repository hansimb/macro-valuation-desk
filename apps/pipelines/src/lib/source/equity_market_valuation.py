from __future__ import annotations

"""ETF fundamentals are point-in-time snapshots, not time series."""

from dataclasses import dataclass
from typing import Any

from src.lib.source.types import SourceError


@dataclass(frozen=True)
class EquityMarketValuationSnapshot:
    provider: str
    symbol: str
    exchange: str | None
    name: str | None
    instrument_type: str | None
    trailing_pe: float | None
    price_to_book: float | None
    price_to_sales: float | None
    price_to_cash_flow: float | None
    dividend_yield_pct: float | None
    price_to_free_cash_flow: float | None
    price_to_cash_flow_method: str
    price_to_free_cash_flow_method: str
    missing_fields: list[str]
    source_url: str = ""
    as_of: str = ""


@dataclass(frozen=True)
class EquityMarketValuationResult:
    ok: bool
    snapshot: EquityMarketValuationSnapshot | None = None
    payload_json: dict[str, Any] | None = None
    error: SourceError | None = None

    @classmethod
    def success(
        cls,
        snapshot: EquityMarketValuationSnapshot,
        *,
        payload_json: dict[str, Any] | None = None,
    ) -> "EquityMarketValuationResult":
        return cls(ok=True, snapshot=snapshot, payload_json=payload_json, error=None)

    @classmethod
    def failure(
        cls,
        *,
        provider: str,
        key: str,
        external_series_id: str,
        error_type: str,
        message: str,
    ) -> "EquityMarketValuationResult":
        return cls(
            ok=False,
            snapshot=None,
            payload_json=None,
            error=SourceError(
                provider=provider,
                key=key,
                external_series_id=external_series_id,
                error_type=error_type,
                message=message,
            ),
        )


_VALUATION_FIELDS = {
    "Price/Prospective Earnings": "trailing_pe",
    "Price/Book": "price_to_book",
    "Price/Sales": "price_to_sales",
    "Price/Cash Flow": "price_to_cash_flow",
    "Dividend-Yield Factor": "dividend_yield_pct",
}


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_eodhd_fundamentals_snapshot(payload: dict[str, Any]) -> EquityMarketValuationSnapshot:
    general = payload.get("General") or {}
    valuations = (payload.get("ETF_Data") or {}).get("Valuations_Growth") or {}

    parsed_values: dict[str, float | None] = {}
    missing_fields: list[str] = []
    for provider_field, snapshot_field in _VALUATION_FIELDS.items():
        parsed_value = _optional_float(valuations.get(provider_field))
        if parsed_value is None:
            parsed_values[snapshot_field] = None
            missing_fields.append(f"ETF_Data.Valuations_Growth.{provider_field}")
            continue

        parsed_values[snapshot_field] = parsed_value

    return EquityMarketValuationSnapshot(
        provider="eodhd",
        symbol=general.get("Code"),
        exchange=general.get("Exchange"),
        name=general.get("Name"),
        instrument_type=general.get("Type"),
        trailing_pe=parsed_values["trailing_pe"],
        price_to_book=parsed_values["price_to_book"],
        price_to_sales=parsed_values["price_to_sales"],
        price_to_cash_flow=parsed_values["price_to_cash_flow"],
        dividend_yield_pct=parsed_values["dividend_yield_pct"],
        price_to_free_cash_flow=None,
        price_to_cash_flow_method="provider_price_to_cash_flow_proxy",
        price_to_free_cash_flow_method="provider_exact_price_to_free_cash_flow_unavailable",
        missing_fields=missing_fields,
    )
