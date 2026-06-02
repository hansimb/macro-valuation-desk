from __future__ import annotations

from datetime import date

from src.lib.source.types import StandardizedSeries


def _normalize_observation_date(raw_date: str) -> str:
    if len(raw_date) == 7:
        return f"{raw_date}-01"

    return date.fromisoformat(raw_date).isoformat()


def stage_standardized_series(series: StandardizedSeries) -> list[dict[str, object]]:
    staged_rows: list[dict[str, object]] = []

    for observation in series.observations:
        try:
            numeric_value = float(observation.value)
        except (TypeError, ValueError):
            continue

        staged_rows.append(
            {
                "series_id": series.key,
                "observation_date": _normalize_observation_date(observation.date),
                "numeric_value": numeric_value,
                "category": series.category,
                "region": series.region,
                "frequency": series.frequency,
                "unit": series.unit,
                "provider": series.provider,
                "is_valid": True,
            }
        )

    return staged_rows
