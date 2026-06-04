import json

from src.lib.source.adapters.dbnomics import DbnomicsAdapter
from src.lib.source.registry import get_series_definition
from src.lib.source.types import FetchOptions


class _FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_dbnomics_adapter_returns_standardized_success(monkeypatch):
    payload = json.dumps(
        {
            "series": {
                "docs": [
                    {
                        "period_start_day": ["2024-01-01", "2025-01-01", "2026-01-01"],
                        "value": ["-0.17", "0.01", "-0.11"],
                    }
                ]
            }
        }
    ).encode("utf-8")

    def fake_urlopen(request):
        assert "api.db.nomics.world/v22/series/AMECO/AVGDGP/USA.1.0.0.0.AVGDGP" in request.full_url
        return _FakeResponse(payload)

    monkeypatch.setattr("src.lib.source.adapters.dbnomics.urlopen", fake_urlopen)

    result = DbnomicsAdapter().fetch_series(
        get_series_definition("us_output_gap"),
        FetchOptions(start_date="2025-01-01"),
    )

    assert result.ok is True
    assert result.error is None
    assert result.series is not None
    assert result.series.key == "us_output_gap"
    assert result.series.provider == "dbnomics"
    assert result.series.series_id == "USA.1.0.0.0.AVGDGP"
    assert [observation.date for observation in result.series.observations] == ["2025-01-01", "2026-01-01"]
    assert result.series.observations[-1].value == "-0.11"
