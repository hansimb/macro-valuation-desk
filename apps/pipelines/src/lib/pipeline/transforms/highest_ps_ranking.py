from __future__ import annotations

import math
from collections import defaultdict


def _round_ratio(value: float) -> float:
    return round(value, 2)


def _round_weight(value: float) -> float:
    return round(value, 1)


def _valid_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    valid_rows: list[dict[str, object]] = []

    for row in rows:
        sector = str(row.get("sector") or "").strip()
        country_code = str(row.get("country_code") or "").strip()
        country_name = str(row.get("country_name") or "").strip()
        if not sector or not country_code or not country_name:
            continue

        try:
            market_cap = float(row["market_cap"])
            traded_value = float(row["average_daily_traded_value"])
            ps_ratio = float(row["ps_ratio"])
            index_weight_pct = float(row["index_weight_pct"])
        except (KeyError, TypeError, ValueError):
            continue

        if market_cap <= 0 or traded_value <= 0 or ps_ratio <= 0 or index_weight_pct <= 0:
            continue

        valid_rows.append(row)

    return valid_rows


def _eligible_rows(rows: list[dict[str, object]], eligibility_fraction: float) -> list[dict[str, object]]:
    if not rows:
        return []

    cutoff = max(1, math.ceil(len(rows) * eligibility_fraction))
    market_cap_sorted = sorted(rows, key=lambda row: float(row["market_cap"]), reverse=True)
    traded_value_sorted = sorted(rows, key=lambda row: float(row["average_daily_traded_value"]), reverse=True)

    market_cap_allowed = {str(row["ticker"]) for row in market_cap_sorted[:cutoff]}
    traded_value_allowed = {str(row["ticker"]) for row in traded_value_sorted[:cutoff]}

    return [row for row in rows if str(row["ticker"]) in market_cap_allowed and str(row["ticker"]) in traded_value_allowed]


def _weighted_average_ps(rows: list[dict[str, object]]) -> float | None:
    if not rows:
        return None

    total_weight = sum(float(row["index_weight_pct"]) for row in rows)
    if total_weight <= 0:
        return None

    weighted_sum = sum(float(row["ps_ratio"]) * float(row["index_weight_pct"]) for row in rows)
    return weighted_sum / total_weight


def build_highest_ps_outputs(
    rows: list[dict[str, object]],
    *,
    ranking_size: int = 25,
    eligibility_fraction: float = 0.4,
) -> dict[str, object]:
    if not rows:
        return {
            "as_of": None,
            "references": [],
            "sections": [],
        }

    rows_by_section: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        rows_by_section[str(row["section_key"])].append(row)

    sections: list[dict[str, object]] = []
    as_of_dates: list[str] = []

    for section_key, section_rows in rows_by_section.items():
        valid_rows = _valid_rows(section_rows)
        eligible_rows = _eligible_rows(valid_rows, eligibility_fraction)
        if not eligible_rows:
            first_row = section_rows[0]
            sections.append(
                {
                    "key": section_key,
                    "label": str(first_row["section_label"]),
                    "universe_key": str(first_row["universe_key"]),
                    "universe_label": str(first_row["universe_label"]),
                    "as_of_date": None,
                    "unavailable": True,
                    "benchmark": {
                        "key": str(first_row["universe_key"]),
                        "label": "S&P 500 Average P/S" if str(first_row["universe_key"]) == "sp500" else "Average P/S",
                        "average_ps_ratio": None,
                        "top_basket_average_ps_ratio": None,
                        "top_basket_index_weight_pct": None,
                        "eligible_constituent_count": 0,
                    },
                    "ranking": [],
                }
            )
            continue

        sector_members: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in eligible_rows:
            sector_members[str(row["sector"])].append(row)

        sector_average_by_name = {
            sector: sum(float(member["ps_ratio"]) for member in members) / len(members)
            for sector, members in sector_members.items()
        }

        ranked_rows = []
        for row in eligible_rows:
            sector_average = sector_average_by_name[str(row["sector"])]
            relative_multiple = float(row["ps_ratio"]) / sector_average
            ranked_rows.append(
                {
                    "ticker": str(row["ticker"]),
                    "company": str(row["company"]),
                    "country_code": str(row["country_code"]),
                    "country_name": str(row["country_name"]),
                    "sector": str(row["sector"]),
                    "ps_ratio": _round_ratio(float(row["ps_ratio"])),
                    "sector_average_ps_ratio": _round_ratio(sector_average),
                    "relative_to_sector_multiple": _round_ratio(relative_multiple),
                    "index_weight_pct": _round_weight(float(row["index_weight_pct"])),
                }
            )

        ranked_rows.sort(
            key=lambda row: (
                row["relative_to_sector_multiple"],
                row["ps_ratio"],
                row["index_weight_pct"],
            ),
            reverse=True,
        )

        top_rows = ranked_rows[:ranking_size]
        ranking = [
            {
                "rank": index + 1,
                **row,
            }
            for index, row in enumerate(top_rows)
        ]

        as_of_date = max(str(row["as_of_date"]) for row in eligible_rows)
        as_of_dates.append(as_of_date)
        top_source_rows = [row for row in eligible_rows if str(row["ticker"]) in {entry["ticker"] for entry in ranking}]
        benchmark_average = _weighted_average_ps(eligible_rows)
        top_basket_average = _weighted_average_ps(top_source_rows)
        top_basket_weight = sum(float(row["index_weight_pct"]) for row in top_source_rows)
        first_row = eligible_rows[0]

        sections.append(
            {
                "key": section_key,
                "label": str(first_row["section_label"]),
                "universe_key": str(first_row["universe_key"]),
                "universe_label": str(first_row["universe_label"]),
                "as_of_date": as_of_date,
                "unavailable": False,
                "benchmark": {
                    "key": str(first_row["universe_key"]),
                    "label": "S&P 500 Average P/S" if str(first_row["universe_key"]) == "sp500" else "Average P/S",
                    "average_ps_ratio": _round_ratio(benchmark_average) if benchmark_average is not None else None,
                    "top_basket_average_ps_ratio": _round_ratio(top_basket_average) if top_basket_average is not None else None,
                    "top_basket_index_weight_pct": _round_weight(top_basket_weight),
                    "eligible_constituent_count": len(eligible_rows),
                },
                "ranking": ranking,
            }
        )

    return {
        "as_of": max(as_of_dates) if as_of_dates else None,
        "references": [],
        "sections": sections,
    }
