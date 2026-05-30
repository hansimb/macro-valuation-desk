from __future__ import annotations

from abc import ABC, abstractmethod

from src.lib.source.types import FetchOptions, FetchResult, SeriesDefinition


class SourceAdapter(ABC):
    @abstractmethod
    def fetch_series(
        self,
        series_definition: SeriesDefinition,
        fetch_options: FetchOptions,
    ) -> FetchResult:
        raise NotImplementedError
