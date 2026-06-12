from src.lib.source.types import FetchResult, Observation, StandardizedSeries
from src.tasks.load_taylor_layers import load_taylor_layers


def test_load_taylor_layers_normalizes_quarterly_raw_observation_dates(monkeypatch):
    fetch_results = [
        FetchResult.success(
            StandardizedSeries(
                key="eu_real_gdp",
                category="growth",
                provider="ecb",
                series_id="MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
                label="Real GDP",
                region="EU",
                frequency="quarterly",
                unit="level",
                source_url="https://data.ecb.europa.eu/data/datasets/MNA/MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
                observations=[
                    Observation(date="1995-Q1", value="100.0"),
                    Observation(date="1995-Q2", value="101.0"),
                ],
            )
        )
    ]
    captured_raw_rows = []
    written_checkpoints = []

    monkeypatch.setattr("src.tasks.load_taylor_layers.utc_now_iso", lambda: "2026-06-12T19:40:00Z")
    monkeypatch.setattr("src.tasks.load_taylor_layers.record_pipeline_run", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.tasks.load_taylor_layers.bootstrap_taylor_rule_schema", lambda connection: None)
    monkeypatch.setattr("src.tasks.load_taylor_layers.upsert_series_metadata", lambda connection, definitions: None)
    monkeypatch.setattr(
        "src.tasks.load_taylor_layers.upsert_raw_observations",
        lambda connection, rows: captured_raw_rows.extend(rows),
    )
    monkeypatch.setattr("src.tasks.load_taylor_layers.upsert_staging_observations", lambda connection, rows: None)
    monkeypatch.setattr("src.tasks.load_taylor_layers.replace_taylor_rule_inputs", lambda connection, rows: None)
    monkeypatch.setattr("src.tasks.load_taylor_layers.replace_macro_reference_metrics", lambda connection, rows: None)
    monkeypatch.setattr(
        "src.tasks.load_taylor_layers.write_successful_checkpoint",
        lambda connection, series_id, last_successful_observation_date, last_run_at: written_checkpoints.append(
            (series_id, last_successful_observation_date)
        ),
    )

    summary = load_taylor_layers.fn(
        object(),
        fetch_results=fetch_results,
        staging_rows=[],
        mart_rows=[],
        reference_metric_rows=[],
    )

    assert summary["raw_rows"] == 2
    assert [row["observation_date"] for row in captured_raw_rows] == ["1995-01-01", "1995-04-01"]
    assert written_checkpoints == [("eu_real_gdp", "1995-04-01")]
