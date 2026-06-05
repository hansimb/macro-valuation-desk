from __future__ import annotations


PAIR_KEY = "eurusd"
PPP_SECTION_KEY = "ppp"
PPP_ITEM_KEY = "relative_ppp"


def _sorted_valid_rows(staging_rows: list[dict[str, object]], series_id: str) -> list[dict[str, object]]:
    return sorted(
        [row for row in staging_rows if row["series_id"] == series_id and row["is_valid"]],
        key=lambda row: str(row["observation_date"]),
    )


def _series_map(staging_rows: list[dict[str, object]], series_id: str) -> dict[str, dict[str, object]]:
    return {str(row["observation_date"]): row for row in _sorted_valid_rows(staging_rows, series_id)}


def _round_price(value: float) -> float:
    return round(value, 4)


def _round_percent(value: float) -> float:
    return round(value, 2)


def build_currency_ppp_outputs(staging_rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    spot_rows = _series_map(staging_rows, "eurusd_spot_monthly")
    us_cpi_rows = _series_map(staging_rows, "us_cpi_index")
    ea_cpi_rows = _series_map(staging_rows, "ea_cpi_index")
    common_months = sorted(set(spot_rows) & set(us_cpi_rows) & set(ea_cpi_rows))

    if not common_months:
        return {
            "snapshot_rows": [],
            "path_rows": [],
            "availability_rows": [
                {
                    "pair_key": PAIR_KEY,
                    "section_key": PPP_SECTION_KEY,
                    "item_key": PPP_ITEM_KEY,
                    "status": "unavailable",
                    "detail": "Required spot or CPI index inputs are unavailable.",
                    "as_of_date": None,
                }
            ],
        }

    latest_month = common_months[-1]
    latest_spot = float(spot_rows[latest_month]["numeric_value"])
    spot_source_url = str(spot_rows[latest_month]["source_url"])
    us_cpi_source_url = str(us_cpi_rows[latest_month]["source_url"])
    ea_cpi_source_url = str(ea_cpi_rows[latest_month]["source_url"])

    snapshot_rows: list[dict[str, object]] = []
    path_rows: list[dict[str, object]] = []

    for base_month in common_months:
        base_spot = float(spot_rows[base_month]["numeric_value"])
        base_us_cpi = float(us_cpi_rows[base_month]["numeric_value"])
        base_ea_cpi = float(ea_cpi_rows[base_month]["numeric_value"])

        for observation_month in [month for month in common_months if month >= base_month]:
            current_us_cpi = float(us_cpi_rows[observation_month]["numeric_value"])
            current_ea_cpi = float(ea_cpi_rows[observation_month]["numeric_value"])
            implied_ppp = base_spot * (current_us_cpi / base_us_cpi) / (current_ea_cpi / base_ea_cpi)

            path_rows.append(
                {
                    "pair_key": PAIR_KEY,
                    "base_month": base_month,
                    "observation_month": observation_month,
                    "actual_spot": _round_price(float(spot_rows[observation_month]["numeric_value"])),
                    "implied_ppp": _round_price(implied_ppp),
                }
            )

        implied_latest = base_spot * (float(us_cpi_rows[latest_month]["numeric_value"]) / base_us_cpi) / (
            float(ea_cpi_rows[latest_month]["numeric_value"]) / base_ea_cpi
        )
        snapshot_rows.append(
            {
                "pair_key": PAIR_KEY,
                "base_month": base_month,
                "as_of_month": latest_month,
                "base_spot": _round_price(base_spot),
                "current_spot": _round_price(latest_spot),
                "implied_ppp": _round_price(implied_latest),
                "deviation_pct": _round_percent(((latest_spot / implied_latest) - 1) * 100),
                "spot_series_key": "eurusd_spot_monthly",
                "spot_source_url": spot_source_url,
                "us_cpi_series_key": "us_cpi_index",
                "us_cpi_source_url": us_cpi_source_url,
                "ea_cpi_series_key": "ea_cpi_index",
                "ea_cpi_source_url": ea_cpi_source_url,
            }
        )

    return {
        "snapshot_rows": snapshot_rows,
        "path_rows": path_rows,
        "availability_rows": [
            {
                "pair_key": PAIR_KEY,
                "section_key": PPP_SECTION_KEY,
                "item_key": PPP_ITEM_KEY,
                "status": "available",
                "detail": "PPP snapshots and paths available.",
                "as_of_date": latest_month,
            }
        ],
    }
