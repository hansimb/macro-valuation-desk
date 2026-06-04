from src.lib.source.types import FetchResult, StandardizedSeries
from src.lib.source.registry import get_series_definition
from src.lib.pipeline.checkpoints import build_fetch_options_for_series
from src.tasks.run_us_macro_core_etl import run_us_macro_core_etl


def test_run_us_macro_core_etl_uses_series_aware_fetch_windows(monkeypatch):
    captured_options = {}

    def fake_fetch_registered_series(definition, fetch_options):
        captured_options[definition.key] = fetch_options
        return FetchResult.success(
            StandardizedSeries(
                key=definition.key,
                category=definition.category,
                provider=definition.provider,
                series_id=definition.external_series_id,
                label=definition.label,
                region=definition.region,
                frequency=definition.frequency,
                unit=definition.unit,
                source_url=definition.source_url,
                observations=[],
            )
        )

    monkeypatch.setattr(
        "src.tasks.run_us_macro_core_etl.read_latest_checkpoint",
        lambda _connection, _series_id: "2026-05-20",
    )
    monkeypatch.setattr(
        "src.tasks.run_us_macro_core_etl.fetch_registered_series",
        fake_fetch_registered_series,
    )

    run_us_macro_core_etl.fn(connection=None)

    assert captured_options["us_policy_rate"].start_date == "2026-04-20"
    assert captured_options["us_cpi_headline"].start_date == "2025-04-15"
    assert captured_options["us_cpi_core"].start_date == "2025-04-15"
    assert captured_options["us_real_gdp"].start_date is None
    assert captured_options["us_output_gap"].start_date == "2026-04-20"


def test_build_fetch_options_for_eu_hicp_headline_uses_index_lookback_when_fallback_is_index():
    options = build_fetch_options_for_series(
        "2026-05-20",
        get_series_definition("eu_hicp_headline"),
    )

    assert options.start_date == "2025-04-15"
