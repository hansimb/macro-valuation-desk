from __future__ import annotations

from datetime import date
from statistics import median

from src.lib.source.types import StandardizedSeries


def _normalize_observation_date(raw_date: str, frequency: str) -> str:
    if len(raw_date) == 7 and raw_date[4] == "-" and raw_date[5] == "Q":
        quarter = int(raw_date[-1])
        month = {1: "01", 2: "04", 3: "07", 4: "10"}[quarter]
        return f"{raw_date[:4]}-{month}-01"

    if frequency == "annual":
        return f"{raw_date[:4]}-01-01"

    if frequency == "quarterly":
        normalized = date.fromisoformat(raw_date).isoformat() if len(raw_date) == 10 else f"{raw_date}-01"
        month = int(normalized[5:7])
        quarter_month = {1: "01", 2: "01", 3: "01", 4: "04", 5: "04", 6: "04", 7: "07", 8: "07", 9: "07", 10: "10", 11: "10", 12: "10"}[month]
        return f"{normalized[:4]}-{quarter_month}-01"

    if frequency == "monthly":
        normalized = date.fromisoformat(raw_date).isoformat() if len(raw_date) == 10 else f"{raw_date}-01"
        return f"{normalized[:7]}-01"

    if len(raw_date) == 7:
        return f"{raw_date}-01"

    return date.fromisoformat(raw_date).isoformat()


def _add_period(value: str, frequency: str, steps: int) -> str:
    year = int(value[:4])
    month = int(value[5:7])
    months_per_step = {"monthly": 1, "quarterly": 3, "annual": 12}[frequency]
    absolute_month = year * 12 + (month - 1) + steps * months_per_step
    next_year = absolute_month // 12
    next_month = (absolute_month % 12) + 1
    return f"{next_year:04d}-{next_month:02d}-01"


def _supports_gap_fill(frequency: str) -> bool:
    return frequency in {"monthly", "quarterly", "annual"}


def fill_series_gaps(staging_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in staging_rows:
        grouped.setdefault(str(row["series_id"]), []).append(row)

    filled_rows: list[dict[str, object]] = []
    for series_rows in grouped.values():
        ordered_rows = sorted(series_rows, key=lambda row: str(row["observation_date"]))
        frequency = str(ordered_rows[0]["frequency"]) if ordered_rows else ""
        row_map = {str(row["observation_date"]): row for row in ordered_rows}
        observed_rows = [row for row in ordered_rows if not bool(row.get("is_imputed", False))]

        if not ordered_rows or not _supports_gap_fill(frequency):
            filled_rows.extend(ordered_rows)
            continue

        current_period = str(ordered_rows[0]["observation_date"])
        final_period = str(ordered_rows[-1]["observation_date"])
        while current_period <= final_period:
            if current_period not in row_map:
                candidate_values = [
                    float(row["numeric_value"])
                    for row in observed_rows
                    if abs(_period_distance(str(row["observation_date"]), current_period, frequency)) <= 6
                ]
                if candidate_values:
                    template_row = ordered_rows[0]
                    row_map[current_period] = {
                        "series_id": template_row["series_id"],
                        "observation_date": current_period,
                        "numeric_value": float(median(candidate_values)),
                        "category": template_row["category"],
                        "region": template_row["region"],
                        "frequency": template_row["frequency"],
                        "unit": template_row["unit"],
                        "provider": template_row["provider"],
                        "source_url": template_row["source_url"],
                        "is_valid": True,
                        "is_imputed": True,
                        "imputation_method": "median_pm_6_periods",
                        "imputation_note": f"Filled using +/- 6 {frequency[:-2] if frequency.endswith('ly') else frequency} median assumption.",
                        "imputation_source_window": f"{_add_period(current_period, frequency, -6)} to {_add_period(current_period, frequency, 6)}",
                    }
            current_period = _add_period(current_period, frequency, 1)

        filled_rows.extend(sorted(row_map.values(), key=lambda row: str(row["observation_date"])))

    return filled_rows


def _period_distance(left: str, right: str, frequency: str) -> int:
    left_year = int(left[:4])
    left_month = int(left[5:7])
    right_year = int(right[:4])
    right_month = int(right[5:7])
    month_delta = (left_year - right_year) * 12 + (left_month - right_month)
    divisor = {"monthly": 1, "quarterly": 3, "annual": 12}[frequency]
    return month_delta // divisor


def stage_standardized_series(series: StandardizedSeries) -> list[dict[str, object]]:
    staged_map: dict[str, dict[str, object]] = {}

    for observation in series.observations:
        try:
            numeric_value = float(observation.value)
        except (TypeError, ValueError):
            continue

        observation_date = _normalize_observation_date(observation.date, series.frequency)
        staged_map[observation_date] = {
            "series_id": series.key,
            "observation_date": observation_date,
            "numeric_value": numeric_value,
            "category": series.category,
            "region": series.region,
            "frequency": series.frequency,
            "unit": series.unit,
            "provider": series.provider,
            "source_url": series.source_url,
            "is_valid": True,
            "is_imputed": False,
            "imputation_method": None,
            "imputation_note": None,
            "imputation_source_window": None,
        }

    return [staged_map[key] for key in sorted(staged_map)]
