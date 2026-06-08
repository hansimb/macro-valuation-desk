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


def _month_key(value: str) -> str:
    return f"{value[:7]}-01"


def _monthly_last_observation_map(staging_rows: list[dict[str, object]], series_id: str) -> dict[str, dict[str, object]]:
    monthly_rows: dict[str, dict[str, object]] = {}
    for row in _sorted_valid_rows(staging_rows, series_id):
        monthly_rows[_month_key(str(row["observation_date"]))] = row
    return monthly_rows


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


def _add_month(value: str, months: int) -> str:
    year = int(value[:4])
    month = int(value[5:7])
    absolute_month = year * 12 + (month - 1) + months
    next_year = absolute_month // 12
    next_month = (absolute_month % 12) + 1
    return f"{next_year:04d}-{next_month:02d}-01"


def _is_consecutive_month_sequence(months: list[str]) -> bool:
    if len(months) < 2:
        return True
    return all(_add_month(months[index - 1], 1) == months[index] for index in range(1, len(months)))


def _trailing_consecutive_months(months: list[str]) -> list[str]:
    if not months:
        return []

    trailing = [months[-1]]
    for index in range(len(months) - 2, -1, -1):
        if _add_month(months[index], 1) != trailing[0]:
            break
        trailing.insert(0, months[index])
    return trailing


def _consecutive_month_runs(months: list[str]) -> list[list[str]]:
    if not months:
        return []

    runs: list[list[str]] = [[months[0]]]
    for month in months[1:]:
        current_run = runs[-1]
        if _add_month(current_run[-1], 1) == month:
            current_run.append(month)
        else:
            runs.append([month])
    return runs


def _latest_consecutive_window(months: list[str], required_months: int) -> list[str]:
    eligible_runs = [run for run in _consecutive_month_runs(months) if len(run) >= required_months]
    if not eligible_runs:
        return []
    latest_run = max(eligible_runs, key=lambda run: run[-1])
    return latest_run[-required_months:]


def _longest_consecutive_window(months: list[str]) -> list[str]:
    runs = _consecutive_month_runs(months)
    if not runs:
        return []
    return max(runs, key=lambda run: (len(run), run[-1]))


def build_currency_ppp_outputs(staging_rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    spot_rows = _monthly_last_observation_map(staging_rows, "eurusd_spot_monthly")
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
            imputed_notes = [
                str(row["imputation_note"])
                for row in (
                    spot_rows[observation_month],
                    us_cpi_rows[observation_month],
                    ea_cpi_rows[observation_month],
                )
                if bool(row.get("is_imputed")) and row.get("imputation_note")
            ]
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
                "has_imputed_inputs": bool(imputed_notes),
                "imputation_note": imputed_notes[0] if imputed_notes else None,
            }
            path_rows.append(path_row)
            anchor_path_rows.append(path_row)

        trailing_12_rows = anchor_path_rows[-12:]
        trailing_12_average_gap = None
        if len(trailing_12_rows) == 12 and _is_consecutive_month_sequence([str(row["observation_month"]) for row in trailing_12_rows]):
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
                "trailing_12m_average_gap_pct": _round_percent(trailing_12_average_gap) if trailing_12_average_gap is not None else None,
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
            year_months = [month for month in common_months if _year_from_month(month) == year]
            if len(year_months) != 12 or not _is_consecutive_month_sequence(year_months):
                continue
            add_anchor(
                anchor_kind="year",
                anchor_statistic=statistic,
                anchor_window_code=None,
                base_year=year,
                anchor_months=year_months,
            )

        for years in WINDOW_OPTIONS:
            required_months = years * 12
            anchor_window_months = _latest_consecutive_window(common_months, required_months)
            if not anchor_window_months:
                continue
            add_anchor(
                anchor_kind="window",
                anchor_statistic=statistic,
                anchor_window_code=f"{years}Y",
                base_year=None,
                anchor_months=anchor_window_months,
            )

        add_anchor(
            anchor_kind="window",
            anchor_statistic=statistic,
            anchor_window_code="MAX",
            base_year=None,
            anchor_months=_longest_consecutive_window(common_months),
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
