from __future__ import annotations


PAIR_KEY = "eurusd"
IRP_SECTION_KEY = "irp"
TENOR_CONFIG = [
    ("3M", "eur_3m_rate", "usd_3m_rate", 0.25),
    ("6M", "eur_6m_rate", "usd_6m_rate", 0.5),
    ("12M", "eur_12m_rate", "usd_12m_rate", 1.0),
]
FORWARD_SERIES_BY_TENOR = {
    "3M": "eurusd_forward_3m",
    "6M": "eurusd_forward_6m",
    "12M": "eurusd_forward_12m",
}


def _latest_row(staging_rows: list[dict[str, object]], series_id: str) -> dict[str, object] | None:
    matching_rows = sorted(
        [row for row in staging_rows if row["series_id"] == series_id and row["is_valid"]],
        key=lambda row: str(row["observation_date"]),
    )
    if not matching_rows:
        return None

    return matching_rows[-1]


def _validated_forward_row(staging_rows: list[dict[str, object]], series_id: str) -> dict[str, object] | None:
    row = _latest_row(staging_rows, series_id)
    if row is None:
        return None

    if row.get("category") != "fx_forward":
        return None
    if bool(row.get("is_imputed", False)):
        return None

    source_url = str(row.get("source_url") or "").strip()
    if not source_url:
        return None

    try:
        numeric_value = float(row["numeric_value"])
    except (TypeError, ValueError):
        return None

    if numeric_value <= 0:
        return None

    return row


def _round_price(value: float) -> float:
    return round(value, 4)


def _round_percent(value: float) -> float:
    return round(value, 2)


def _round_basis_points(value: float) -> float:
    return round(value, 1)


def _build_unavailable_rows() -> list[dict[str, object]]:
    return [
        {
            "pair_key": PAIR_KEY,
            "section_key": IRP_SECTION_KEY,
            "item_key": tenor,
            "status": "unavailable",
            "detail": "Required spot or tenor rate inputs are unavailable.",
            "as_of_date": None,
        }
        for tenor, _eur_key, _usd_key, _tenor_fraction in TENOR_CONFIG
    ]


def build_currency_irp_outputs(staging_rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    spot_row = _latest_row(staging_rows, "eurusd_spot_daily")
    if spot_row is None:
        return {"snapshot_rows": [], "availability_rows": _build_unavailable_rows()}

    spot = float(spot_row["numeric_value"])
    spot_observation_date = str(spot_row["observation_date"])
    spot_source_url = str(spot_row["source_url"])

    snapshot_rows: list[dict[str, object]] = []
    availability_rows: list[dict[str, object]] = []

    for tenor, eur_series_key, usd_series_key, tenor_fraction in TENOR_CONFIG:
        eur_row = _latest_row(staging_rows, eur_series_key)
        usd_row = _latest_row(staging_rows, usd_series_key)
        if eur_row is None or usd_row is None:
            availability_rows.append(
                {
                    "pair_key": PAIR_KEY,
                    "section_key": IRP_SECTION_KEY,
                    "item_key": tenor,
                    "status": "unavailable",
                    "detail": "Required spot or tenor rate inputs are unavailable.",
                    "as_of_date": None,
                }
            )
            continue

        eur_rate = float(eur_row["numeric_value"])
        usd_rate = float(usd_row["numeric_value"])
        rate_spread = eur_rate - usd_rate
        cip_implied_forward = spot * ((1 + (eur_rate / 100) * tenor_fraction) / (1 + (usd_rate / 100) * tenor_fraction))
        forward_series_key = FORWARD_SERIES_BY_TENOR[tenor]
        forward_row = _validated_forward_row(staging_rows, forward_series_key)
        observed_forward = float(forward_row["numeric_value"]) if forward_row is not None else None
        cip_basis_bps = (
            ((observed_forward - cip_implied_forward) / spot) * 10000
            if observed_forward is not None
            else None
        )
        uip_implied_move_pct = rate_spread * tenor_fraction
        uip_implied_spot = spot * (1 + (uip_implied_move_pct / 100))

        snapshot_rows.append(
            {
                "pair_key": PAIR_KEY,
                "as_of_date": spot_observation_date,
                "tenor": tenor,
                "spot": _round_price(spot),
                "eur_rate": _round_percent(eur_rate),
                "usd_rate": _round_percent(usd_rate),
                "rate_spread": _round_percent(rate_spread),
                "cip_implied_forward": _round_price(cip_implied_forward),
                "observed_forward": _round_price(observed_forward) if observed_forward is not None else None,
                "cip_basis_bps": _round_basis_points(cip_basis_bps) if cip_basis_bps is not None else None,
                "uip_implied_move_pct": _round_percent(uip_implied_move_pct),
                "uip_implied_spot": _round_price(uip_implied_spot),
                "spot_series_key": "eurusd_spot_daily",
                "spot_source_url": spot_source_url,
                "eur_rate_series_key": eur_series_key,
                "eur_rate_source_url": str(eur_row["source_url"]),
                "usd_rate_series_key": usd_series_key,
                "usd_rate_source_url": str(usd_row["source_url"]),
                "forward_series_key": forward_series_key if forward_row is not None else None,
                "forward_source_url": str(forward_row["source_url"]) if forward_row is not None else None,
                "has_observed_forward": forward_row is not None,
            }
        )
        availability_rows.append(
            {
                "pair_key": PAIR_KEY,
                "section_key": IRP_SECTION_KEY,
                "item_key": tenor,
                "status": "available" if forward_row is not None else "partial",
                "detail": (
                    "Observed forward comparison available."
                    if forward_row is not None
                    else "Observed forward unavailable; CIP-only comparison returned."
                ),
                "as_of_date": spot_observation_date,
            }
        )

    return {"snapshot_rows": snapshot_rows, "availability_rows": availability_rows}
