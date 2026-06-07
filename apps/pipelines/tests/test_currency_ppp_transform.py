from src.lib.pipeline.transforms.currency_ppp import build_currency_ppp_outputs


def _build_monthly_rows():
    rows = []

    for year in range(2000, 2027):
        last_month = 4 if year == 2026 else 12
        for month in range(1, last_month + 1):
            date = f"{year}-{month:02d}-01"
            month_index = (year - 2000) * 12 + (month - 1)
            spot = 0.9 + month_index * 0.001
            us_cpi = 100 + month_index * 0.2
            ea_cpi = 98 + month_index * 0.15

            rows.extend(
                [
                    {
                        "series_id": "eurusd_spot_monthly",
                        "observation_date": date,
                        "numeric_value": spot,
                        "category": "fx_spot",
                        "region": "FX",
                        "frequency": "monthly",
                        "unit": "usd_per_eur",
                        "provider": "ecb",
                        "source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
                        "is_valid": True,
                    },
                    {
                        "series_id": "us_cpi_index",
                        "observation_date": date,
                        "numeric_value": us_cpi,
                        "category": "inflation",
                        "region": "US",
                        "frequency": "monthly",
                        "unit": "index",
                        "provider": "fred",
                        "source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
                        "is_valid": True,
                    },
                    {
                        "series_id": "ea_cpi_index",
                        "observation_date": date,
                        "numeric_value": ea_cpi,
                        "category": "inflation",
                        "region": "EU",
                        "frequency": "monthly",
                        "unit": "index",
                        "provider": "fred",
                        "source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
                        "is_valid": True,
                    },
                ]
            )

    return rows


def test_build_currency_ppp_outputs_creates_year_window_and_max_anchors():
    outputs = build_currency_ppp_outputs(_build_monthly_rows())

    snapshots = outputs["snapshot_rows"]
    paths = outputs["path_rows"]

    assert outputs["availability_rows"] == [
        {
            "pair_key": "eurusd",
            "section_key": "ppp",
            "item_key": "relative_ppp",
            "status": "available",
            "detail": "PPP snapshots and paths available.",
            "as_of_date": "2026-04-01",
        }
    ]

    snapshot_keys = {
        (
            row["anchor_kind"],
            row["anchor_statistic"],
            row["anchor_window_code"],
            row["base_year"],
        )
        for row in snapshots
    }

    assert ("window", "average", "20Y", None) in snapshot_keys
    assert ("window", "median", "20Y", None) in snapshot_keys
    assert ("window", "average", "MAX", None) in snapshot_keys
    assert ("window", "median", "MAX", None) in snapshot_keys
    assert ("year", "average", None, "2025") in snapshot_keys
    assert ("year", "median", None, "2025") in snapshot_keys

    max_snapshot = next(
        row
        for row in snapshots
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "MAX"
    )
    assert max_snapshot["anchor_start_month"] == "2000-01-01"
    assert max_snapshot["anchor_end_month"] == "2026-04-01"
    assert max_snapshot["anchor_years_covered"] == 26
    assert max_snapshot["as_of_month"] == "2026-04-01"

    twenty_year_path = [
        row
        for row in paths
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "20Y"
    ]
    assert twenty_year_path[0]["observation_month"] == "2006-05-01"
    assert twenty_year_path[-1]["observation_month"] == "2026-04-01"


def test_build_currency_ppp_outputs_marks_series_unavailable_when_required_inputs_are_missing():
    outputs = build_currency_ppp_outputs([])

    assert outputs["snapshot_rows"] == []
    assert outputs["path_rows"] == []
    assert outputs["availability_rows"] == [
        {
            "pair_key": "eurusd",
            "section_key": "ppp",
            "item_key": "relative_ppp",
            "status": "unavailable",
            "detail": "Required spot or CPI index inputs are unavailable.",
            "as_of_date": None,
        }
    ]


def test_build_currency_ppp_outputs_normalizes_daily_spot_to_consecutive_monthly_path():
    rows = []

    for month in range(1, 13):
        month_start = f"2025-{month:02d}-01"
        month_end = f"2025-{month:02d}-28"
        spot_value = 1.0 + month * 0.01

        rows.extend(
            [
                {
                    "series_id": "eurusd_spot_monthly",
                    "observation_date": month_start,
                    "numeric_value": spot_value - 0.005,
                    "category": "fx_spot",
                    "region": "FX",
                    "frequency": "monthly",
                    "unit": "usd_per_eur",
                    "provider": "ecb",
                    "source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
                    "is_valid": True,
                },
                {
                    "series_id": "eurusd_spot_monthly",
                    "observation_date": month_end,
                    "numeric_value": spot_value,
                    "category": "fx_spot",
                    "region": "FX",
                    "frequency": "monthly",
                    "unit": "usd_per_eur",
                    "provider": "ecb",
                    "source_url": "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A",
                    "is_valid": True,
                },
                {
                    "series_id": "us_cpi_index",
                    "observation_date": month_start,
                    "numeric_value": 100 + month,
                    "category": "inflation",
                    "region": "US",
                    "frequency": "monthly",
                    "unit": "index",
                    "provider": "fred",
                    "source_url": "https://fred.stlouisfed.org/series/CPIAUCSL",
                    "is_valid": True,
                },
                {
                    "series_id": "ea_cpi_index",
                    "observation_date": month_start,
                    "numeric_value": 99 + month * 0.8,
                    "category": "inflation",
                    "region": "EU",
                    "frequency": "monthly",
                    "unit": "index",
                    "provider": "fred",
                    "source_url": "https://fred.stlouisfed.org/series/CP00MI15EA20M086NEST",
                    "is_valid": True,
                },
            ]
        )

    outputs = build_currency_ppp_outputs(rows)

    max_snapshot = next(
        row
        for row in outputs["snapshot_rows"]
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "MAX"
    )
    max_path = [
        row
        for row in outputs["path_rows"]
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "MAX"
    ]

    assert [row["observation_month"] for row in max_path] == [f"2025-{month:02d}-01" for month in range(1, 13)]
    assert max_path[-1]["actual_spot"] == 1.12
    assert max_snapshot["trailing_12m_average_gap_pct"] is not None


def test_build_currency_ppp_outputs_does_not_claim_trailing_12m_when_common_months_have_gap():
    rows = _build_monthly_rows()
    rows = [
        row
        for row in rows
        if not (row["series_id"] == "us_cpi_index" and row["observation_date"] == "2025-10-01")
    ]

    outputs = build_currency_ppp_outputs(rows)

    max_snapshot = next(
        row
        for row in outputs["snapshot_rows"]
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "MAX"
    )

    assert max_snapshot["trailing_12m_average_gap_pct"] is None


def test_build_currency_ppp_outputs_requires_consecutive_months_for_window_and_year_anchors():
    rows = _build_monthly_rows()
    rows = [
        row
        for row in rows
        if not (
            (row["series_id"] == "us_cpi_index" and row["observation_date"] == "2025-10-01")
            or (row["series_id"] == "ea_cpi_index" and row["observation_date"] == "2025-10-01")
        )
    ]

    outputs = build_currency_ppp_outputs(rows)
    snapshot_keys = {
        (
            row["anchor_kind"],
            row["anchor_statistic"],
            row["anchor_window_code"],
            row["base_year"],
        )
        for row in outputs["snapshot_rows"]
    }

    assert ("window", "average", "20Y", None) in snapshot_keys
    assert ("window", "average", "3Y", None) in snapshot_keys
    assert ("year", "average", None, "2025") not in snapshot_keys

    max_snapshot = next(
        row
        for row in outputs["snapshot_rows"]
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "MAX"
    )
    assert max_snapshot["anchor_start_month"] == "2000-01-01"
    assert max_snapshot["anchor_end_month"] == "2025-09-01"

    twenty_year_snapshot = next(
        row
        for row in outputs["snapshot_rows"]
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "20Y"
    )
    assert twenty_year_snapshot["anchor_start_month"] == "2005-10-01"
    assert twenty_year_snapshot["anchor_end_month"] == "2025-09-01"

    three_year_snapshot = next(
        row
        for row in outputs["snapshot_rows"]
        if row["anchor_kind"] == "window"
        and row["anchor_statistic"] == "average"
        and row["anchor_window_code"] == "3Y"
    )
    assert three_year_snapshot["anchor_start_month"] == "2022-10-01"
    assert three_year_snapshot["anchor_end_month"] == "2025-09-01"
