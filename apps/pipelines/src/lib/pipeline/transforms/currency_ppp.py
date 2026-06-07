from __future__ import annotations


PAIR_KEY = "eurusd"
PPP_SECTION_KEY = "ppp"
PPP_ITEM_KEY = "relative_ppp"
WINDOW_OPTIONS = [3, 5, 10, 20]
ANCHOR_STATISTICS = ["average", "median"]


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


def _year_from_month(value: str) -> str:
    return value[:4]


def _average(values: list[float]) -> float:
    return sum(values) / len(values)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _aggregate(values: list[float], statistic: str) -> float:
    return _median(values) if statistic == "median" else _average(values)


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

    def add_anchor(
        *,
        anchor_kind: str,
        anchor_statistic: str,
        anchor_window_code: str | None,
        base_year: str | None,
        anchor_months: list[str],
    ) -> None:
        if not anchor_months:
            return

        anchor_start_month = anchor_months[0]
        anchor_end_month = anchor_months[-1]
        base_month = anchor_start_month
        anchor_years_covered = max(1, round(len(anchor_months) / 12))

        base_spot = _aggregate([float(spot_rows[month]["numeric_value"]) for month in anchor_months], anchor_statistic)
        base_us_cpi = _aggregate([float(us_cpi_rows[month]["numeric_value"]) for month in anchor_months], anchor_statistic)
        base_ea_cpi = _aggregate([float(ea_cpi_rows[month]["numeric_value"]) for month in anchor_months], anchor_statistic)

        anchor_path_rows: list[dict[str, object]] = []
        for observation_month in [month for month in common_months if month >= anchor_start_month]:
            current_us_cpi = float(us_cpi_rows[observation_month]["numeric_value"])
            current_ea_cpi = float(ea_cpi_rows[observation_month]["numeric_value"])
            implied_ppp = base_spot * (current_us_cpi / base_us_cpi) / (current_ea_cpi / base_ea_cpi)

            path_row = {
                "pair_key": PAIR_KEY,
                "base_month": base_month,
                "anchor_kind": anchor_kind,
                "anchor_statistic": anchor_statistic,
                "anchor_window_code": anchor_window_code,
                "base_year": base_year,
                "observation_month": observation_month,
                "actual_spot": _round_price(float(spot_rows[observation_month]["numeric_value"])),
                "implied_ppp": _round_price(implied_ppp),
            }
            path_rows.append(path_row)
            anchor_path_rows.append(path_row)

        trailing_12_rows = anchor_path_rows[-12:]
        trailing_12_average_gap = _average(
            [
                ((float(row["actual_spot"]) / float(row["implied_ppp"])) - 1) * 100
                for row in trailing_12_rows
                if float(row["implied_ppp"]) != 0
            ]
        )
        implied_latest = float(anchor_path_rows[-1]["implied_ppp"])

        snapshot_rows.append(
            {
                "pair_key": PAIR_KEY,
                "base_month": base_month,
                "anchor_kind": anchor_kind,
                "anchor_statistic": anchor_statistic,
                "anchor_window_code": anchor_window_code,
                "anchor_start_month": anchor_start_month,
                "anchor_end_month": anchor_end_month,
                "anchor_years_covered": anchor_years_covered,
                "base_year": base_year,
                "as_of_month": latest_month,
                "base_spot": _round_price(base_spot),
                "current_spot": _round_price(latest_spot),
                "implied_ppp": _round_price(implied_latest),
                "deviation_pct": _round_percent(((latest_spot / implied_latest) - 1) * 100),
                "trailing_12m_average_gap_pct": _round_percent(trailing_12_average_gap),
                "spot_series_key": "eurusd_spot_monthly",
                "spot_source_url": spot_source_url,
                "us_cpi_series_key": "us_cpi_index",
                "us_cpi_source_url": us_cpi_source_url,
                "ea_cpi_series_key": "ea_cpi_index",
                "ea_cpi_source_url": ea_cpi_source_url,
            }
        )

    for statistic in ANCHOR_STATISTICS:
        for year in sorted({_year_from_month(month) for month in common_months}):
            add_anchor(
                anchor_kind="year",
                anchor_statistic=statistic,
                anchor_window_code=None,
                base_year=year,
                anchor_months=[month for month in common_months if _year_from_month(month) == year],
            )

        for years in WINDOW_OPTIONS:
            required_months = years * 12
            if len(common_months) < required_months:
                continue
            add_anchor(
                anchor_kind="window",
                anchor_statistic=statistic,
                anchor_window_code=f"{years}Y",
                base_year=None,
                anchor_months=common_months[-required_months:],
            )

        add_anchor(
            anchor_kind="window",
            anchor_statistic=statistic,
            anchor_window_code="MAX",
            base_year=None,
            anchor_months=common_months,
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
