from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeriesDefinition:
    key: str
    category: str
    provider: str
    external_series_id: str
    label: str
    region: str
    frequency: str
    unit: str
    source_url: str


@dataclass(frozen=True)
class FetchOptions:
    start_date: str | None = None
    end_date: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class Observation:
    date: str
    value: str


@dataclass(frozen=True)
class StandardizedSeries:
    key: str
    category: str
    provider: str
    series_id: str
    label: str
    region: str
    frequency: str
    unit: str
    source_url: str
    observations: list[Observation]


@dataclass(frozen=True)
class SourceError:
    provider: str
    key: str
    external_series_id: str
    error_type: str
    message: str


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    series: StandardizedSeries | None = None
    error: SourceError | None = None

    @classmethod
    def success(cls, series: StandardizedSeries) -> "FetchResult":
        return cls(ok=True, series=series, error=None)

    @classmethod
    def failure(
        cls,
        *,
        provider: str,
        key: str,
        external_series_id: str,
        error_type: str,
        message: str,
    ) -> "FetchResult":
        return cls(
            ok=False,
            series=None,
            error=SourceError(
                provider=provider,
                key=key,
                external_series_id=external_series_id,
                error_type=error_type,
                message=message,
            ),
        )
