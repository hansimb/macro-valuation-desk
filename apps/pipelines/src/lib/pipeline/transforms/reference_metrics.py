from __future__ import annotations

from datetime import date

from src.lib.source.registry import get_series_definition

POLICY_REAL_RATE_NOTE = "Policy real rate = policy rate minus headline inflation."
MARKET_REAL_RATE_HEADLINE_PROXY_SERIES = {"eu_market_real_rate"}


def _sorted_valid_rows(staging_rows: list[dict[str, object]], series_id: str) -> list[dict[str, object]]:
    return sorted(
        [row for row in staging_rows if row["series_id"] == series_id and row["is_valid"]],
        key=lambda row: str(row["observation_date"]),
    )


def _latest_row(staging_rows: list[dict[str, object]], series_id: str) -> dict[str, object]:
    return _sorted_valid_rows(staging_rows, series_id)[-1]


def _round_rate(value: float) -> float:
    return round(value, 2)


def _format_history_window(dates: list[str]) -> str:
    if len(dates) == 1:
        return dates[0]

    return f"{dates[0]} to {dates[-1]}"


def _minus_one_year(iso_date: str) -> str:
    observed_at = date.fromisoformat(iso_date)
    return observed_at.replace(year=observed_at.year - 1).isoformat()


def _latest_inflation_rate(staging_rows: list[dict[str, object]], series_id: str) -> tuple[float, str]:
    rows = _sorted_valid_rows(staging_rows, series_id)
    latest_row = rows[-1]
    latest_date = str(latest_row["observation_date"])
    latest_value = float(latest_row["numeric_value"])

    if latest_row["unit"] != "index":
        return _round_rate(latest_value), latest_date

    values_by_date = {str(row["observation_date"]): float(row["numeric_value"]) for row in rows}
    previous_value = values_by_date[_minus_one_year(latest_date)]

    return _round_rate(((latest_value / previous_value) - 1) * 100), latest_date


def _latest_market_real_rate(
    staging_rows: list[dict[str, object]],
    series_id: str,
    headline_inflation: float,
) -> tuple[float, str]:
    latest_row = _latest_row(staging_rows, series_id)
    latest_value = float(latest_row["numeric_value"])
    latest_date = str(latest_row["observation_date"])

    if series_id in MARKET_REAL_RATE_HEADLINE_PROXY_SERIES:
        return _round_rate(latest_value - headline_inflation), latest_date

    return _round_rate(latest_value), latest_date


def _series_rates_from_level(
    staging_rows: list[dict[str, object]],
    series_id: str,
) -> tuple[tuple[float, float, str, str], tuple[float, float, str, str]]:
    rows = _sorted_valid_rows(staging_rows, series_id)
    values_by_date = {str(row["observation_date"]): float(row["numeric_value"]) for row in rows}
    ordered_dates = [str(row["observation_date"]) for row in rows]

    yoy_rates: list[tuple[str, float]] = []
    qoq_rates: list[tuple[str, float]] = []

    for index, current_date in enumerate(ordered_dates):
        current_value = values_by_date[current_date]
        prior_year_date = _minus_one_year(current_date)
        if prior_year_date in values_by_date:
            prior_year_value = values_by_date[prior_year_date]
            yoy_rates.append((current_date, _round_rate(((current_value / prior_year_value) - 1) * 100)))

        if index == 0:
            continue

        previous_date = ordered_dates[index - 1]
        previous_value = values_by_date[previous_date]
        qoq_rates.append((current_date, _round_rate((((current_value / previous_value) ** 4) - 1) * 100)))

    latest_yoy_date, latest_yoy_value = yoy_rates[-1]
    latest_qoq_date, latest_qoq_value = qoq_rates[-1]

    yoy_average = _round_rate(sum(rate for _, rate in yoy_rates) / len(yoy_rates))
    qoq_average = _round_rate(sum(rate for _, rate in qoq_rates) / len(qoq_rates))

    return (
        (
            latest_yoy_value,
            yoy_average,
            latest_yoy_date,
            _format_history_window([date_key for date_key, _ in yoy_rates]),
        ),
        (
            latest_qoq_value,
            qoq_average,
            latest_qoq_date,
            _format_history_window([date_key for date_key, _ in qoq_rates]),
        ),
    )


def build_macro_reference_metrics(staging_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    region_series_map = {
        "EU": {
            "policy": "eu_policy_rate",
            "headline": "eu_hicp_headline",
            "core": "eu_hicp_core",
            "market_real_rate": "eu_market_real_rate",
            "gdp": "eu_real_gdp",
        },
        "US": {
            "policy": "us_policy_rate",
            "headline": "us_cpi_headline",
            "core": "us_cpi_core",
            "market_real_rate": "us_market_real_rate",
            "gdp": "us_real_gdp",
        },
    }
    rows: list[dict[str, object]] = []

    for region, series_map in sorted(region_series_map.items()):
        policy_rate = float(_latest_row(staging_rows, series_map["policy"])["numeric_value"])
        headline_inflation, headline_as_of = _latest_inflation_rate(staging_rows, series_map["headline"])
        core_inflation, core_as_of = _latest_inflation_rate(staging_rows, series_map["core"])
        market_real_rate, market_real_rate_as_of = _latest_market_real_rate(
            staging_rows,
            series_map["market_real_rate"],
            headline_inflation,
        )
        (gdp_yoy_current, gdp_yoy_average, gdp_yoy_as_of, gdp_yoy_window), (
            gdp_qoq_current,
            gdp_qoq_average,
            gdp_qoq_as_of,
            gdp_qoq_window,
        ) = _series_rates_from_level(staging_rows, series_map["gdp"])

        headline_definition = get_series_definition(series_map["headline"])
        core_definition = get_series_definition(series_map["core"])
        market_real_definition = get_series_definition(series_map["market_real_rate"])
        gdp_definition = get_series_definition(series_map["gdp"])

        rows.append(
            {
                "region": region,
                "headline_inflation": headline_inflation,
                "headline_inflation_as_of_date": headline_as_of,
                "core_inflation": core_inflation,
                "core_inflation_as_of_date": core_as_of,
                "policy_real_rate": _round_rate(policy_rate - headline_inflation),
                "policy_real_rate_as_of_date": max(str(_latest_row(staging_rows, series_map["policy"])["observation_date"]), headline_as_of),
                "market_real_rate": market_real_rate,
                "market_real_rate_as_of_date": market_real_rate_as_of,
                "gdp_growth_yoy_current": gdp_yoy_current,
                "gdp_growth_yoy_historical_average": gdp_yoy_average,
                "gdp_growth_yoy_gap": _round_rate(gdp_yoy_current - gdp_yoy_average),
                "gdp_growth_yoy_as_of_date": gdp_yoy_as_of,
                "gdp_growth_yoy_history_window": gdp_yoy_window,
                "gdp_growth_qoq_annualized_current": gdp_qoq_current,
                "gdp_growth_qoq_annualized_historical_average": gdp_qoq_average,
                "gdp_growth_qoq_annualized_gap": _round_rate(gdp_qoq_current - gdp_qoq_average),
                "gdp_growth_qoq_annualized_as_of_date": gdp_qoq_as_of,
                "gdp_growth_qoq_annualized_history_window": gdp_qoq_window,
                "headline_series_key": headline_definition.key,
                "headline_source_url": headline_definition.source_url,
                "core_series_key": core_definition.key,
                "core_source_url": core_definition.source_url,
                "market_real_rate_series_key": market_real_definition.key,
                "market_real_rate_source_url": market_real_definition.source_url,
                "gdp_series_key": gdp_definition.key,
                "gdp_source_url": gdp_definition.source_url,
                "policy_real_rate_note": POLICY_REAL_RATE_NOTE,
            }
        )

    return rows
