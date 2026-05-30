import json

from src.lib.source.adapters.fred import FredAdapter
from src.lib.source.fetch import fetch_registered_series
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


def test_fred_adapter_returns_standardized_success(monkeypatch):
    payload = json.dumps(
        {
            "observations": [
                {"date": "2026-05-01", "value": "4.50"},
                {"date": "2026-05-02", "value": "4.50"},
            ]
        }
    ).encode("utf-8")

    def fake_urlopen(request):
        assert "series_id=DFEDTARU" in request.full_url
        assert "observation_start=2026-05-01" in request.full_url
        return _FakeResponse(payload)

    monkeypatch.setattr("src.lib.source.adapters.fred.urlopen", fake_urlopen)

    result = FredAdapter().fetch_series(
        get_series_definition("us_policy_rate"),
        FetchOptions(start_date="2026-05-01"),
    )

    assert result.ok is True
    assert result.error is None
    assert result.series is not None
    assert result.series.key == "us_policy_rate"
    assert result.series.provider == "fred"
    assert result.series.series_id == "DFEDTARU"
    assert result.series.observations[0].date == "2026-05-01"
    assert result.series.observations[0].value == "4.50"


def test_fetch_registered_series_returns_structured_adapter_failure(monkeypatch):
    def fake_urlopen(_request):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("src.lib.source.adapters.fred.urlopen", fake_urlopen)

    result = fetch_registered_series(
        get_series_definition("us_cpi_headline"),
        FetchOptions(),
    )

    assert result.ok is False
    assert result.series is None
    assert result.error is not None
    assert result.error.provider == "fred"
    assert result.error.key == "us_cpi_headline"
    assert result.error.external_series_id == "CPIAUCSL"
    assert result.error.error_type == "fetch_error"
    assert "provider unavailable" in result.error.message
