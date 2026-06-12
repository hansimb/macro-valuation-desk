from src.lib.source.fetch import fetch_registered_series
from src.lib.source.registry import get_series_definition
from src.lib.source.types import FetchOptions, FetchResult, StandardizedSeries, Observation


def test_fetch_registered_series_uses_fallback_source_when_primary_fails(monkeypatch, capsys):
    series_definition = get_series_definition("eu_hicp_core")
    calls: list[str] = []

    def fake_ecb_fetch(_series_definition, _fetch_options):
        calls.append("ecb")
        return FetchResult.failure(
            provider="ecb",
            key="eu_hicp_core",
            external_series_id="HICP.M.U2.N.XEF000.4D0.ANR",
            error_type="fetch_error",
            message="blocked",
        )

    def fake_fred_fetch(series_definition, _fetch_options):
        calls.append("fred")
        return FetchResult.success(
            StandardizedSeries(
                key=series_definition.key,
                category=series_definition.category,
                provider=series_definition.provider,
                series_id=series_definition.external_series_id,
                label=series_definition.label,
                region=series_definition.region,
                frequency=series_definition.frequency,
                unit=series_definition.unit,
                source_url=series_definition.source_url,
                observations=[Observation(date="2026-04-01", value="102.35")],
            )
        )

    monkeypatch.setattr("src.lib.source.fetch.ADAPTERS", {"ecb": type("A", (), {"fetch_series": staticmethod(fake_ecb_fetch)})(), "fred": type("B", (), {"fetch_series": staticmethod(fake_fred_fetch)})()})

    result = fetch_registered_series(series_definition, FetchOptions())

    assert result.ok is True
    assert result.series is not None
    assert result.series.provider == "fred"
    assert result.series.series_id == "00XEFDEZCCM086NEST"
    assert result.series.source_url == "https://fred.stlouisfed.org/series/00XEFDEZCCM086NEST"
    assert calls == ["ecb", "fred"]
    warning = capsys.readouterr().err
    assert "WARNING:" in warning
    assert "eu_hicp_core" in warning
    assert "primary provider ecb failed" in warning
    assert "using fallback provider fred" in warning
    assert "blocked" in warning


def test_fetch_registered_series_reports_both_primary_and_fallback_failures(monkeypatch):
    series_definition = get_series_definition("eu_policy_rate")

    def fake_fail(series_definition, _fetch_options):
        return FetchResult.failure(
            provider=series_definition.provider,
            key=series_definition.key,
            external_series_id=series_definition.external_series_id,
            error_type="fetch_error",
            message=f"{series_definition.provider} failed",
        )

    monkeypatch.setattr("src.lib.source.fetch.ADAPTERS", {"ecb": type("A", (), {"fetch_series": staticmethod(fake_fail)})(), "fred": type("B", (), {"fetch_series": staticmethod(fake_fail)})()})

    result = fetch_registered_series(series_definition, FetchOptions())

    assert result.ok is False
    assert result.error is not None
    assert "Primary source failed: ecb failed" in result.error.message
    assert "Fallback source failed: fred failed" in result.error.message
