from __future__ import annotations

from datetime import date

DEFAULT_NEUTRAL_RATE = 1.0
DEFAULT_INFLATION_TARGET = 2.0
DEFAULT_SLACK_PROXY = 0.0
DEFAULT_INFLATION_WEIGHT = 0.5
DEFAULT_SLACK_WEIGHT = 0.5
DEFAULT_SLACK_SOURCE_NOTE = "Assumed neutral slack proxy in v1"


def _latest_row_by_series(staging_rows: list[dict[str, object]], series_id: str) -> dict[str, object]:
    matching_rows = [row for row in staging_rows if row["series_id"] == series_id and row["is_valid"]]
    return sorted(matching_rows, key=lambda row: str(row["observation_date"]))[-1]


def _latest_inflation_value(staging_rows: list[dict[str, object]], series_id: str) -> tuple[float, str]:
    matching_rows = sorted(
        [row for row in staging_rows if row["series_id"] == series_id and row["is_valid"]],
        key=lambda row: str(row["observation_date"]),
    )
    latest_row = matching_rows[-1]
    latest_date = str(latest_row["observation_date"])
    latest_value = float(latest_row["numeric_value"])

    if latest_row["unit"] != "index":
        return round(latest_value, 2), latest_date

    prior_year_date = date.fromisoformat(latest_date).replace(year=date.fromisoformat(latest_date).year - 1).isoformat()
    prior_year_value = next(
        float(row["numeric_value"])
        for row in matching_rows
        if str(row["observation_date"]) == prior_year_date
    )

    return round(((latest_value / prior_year_value) - 1) * 100, 2), latest_date


def build_taylor_rule_inputs(staging_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    region_series_map = {
        "EU": ("eu_policy_rate", "eu_hicp_headline"),
        "US": ("us_policy_rate", "us_cpi_headline"),
    }
    mart_rows: list[dict[str, object]] = []

    for region, (policy_series_key, inflation_series_key) in sorted(region_series_map.items()):
        policy_row = _latest_row_by_series(staging_rows, policy_series_key)
        inflation, inflation_as_of = _latest_inflation_value(staging_rows, inflation_series_key)

        policy_rate = float(policy_row["numeric_value"])
        implied_rate = round(
            DEFAULT_NEUTRAL_RATE
            + inflation
            + DEFAULT_INFLATION_WEIGHT * (inflation - DEFAULT_INFLATION_TARGET)
            + DEFAULT_SLACK_WEIGHT * DEFAULT_SLACK_PROXY,
            2,
        )
        policy_gap = round(policy_rate - implied_rate, 2)

        mart_rows.append(
            {
                "region": region,
                "as_of_date": max(str(policy_row["observation_date"]), inflation_as_of),
                "policy_rate": policy_rate,
                "inflation": inflation,
                "inflation_target": DEFAULT_INFLATION_TARGET,
                "neutral_rate": DEFAULT_NEUTRAL_RATE,
                "slack_proxy": DEFAULT_SLACK_PROXY,
                "implied_rate": implied_rate,
                "policy_gap": policy_gap,
                "policy_series_key": policy_series_key,
                "policy_source_url": str(policy_row["source_url"]),
                "inflation_series_key": inflation_series_key,
                "inflation_source_url": str(_latest_row_by_series(staging_rows, inflation_series_key)["source_url"]),
                "slack_source_note": DEFAULT_SLACK_SOURCE_NOTE,
            }
        )

    return mart_rows
