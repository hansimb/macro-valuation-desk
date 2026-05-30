import csv
import io

from src.lib.source.adapters.ecb import EcbAdapter
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


def test_ecb_adapter_returns_standardized_success(monkeypatch):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["TIME_PERIOD", "OBS_VALUE"])
    writer.writeheader()
    writer.writerow({"TIME_PERIOD": "2026-03", "OBS_VALUE": "2.20"})
    writer.writerow({"TIME_PERIOD": "2026-04", "OBS_VALUE": "2.10"})

    def fake_urlopen(request):
        assert "FM.D.U2.EUR.4F.KR.DFR.LEV" in request.full_url
        assert "startPeriod=2026-01-01" in request.full_url
        return _FakeResponse(output.getvalue().encode("utf-8"))

    monkeypatch.setattr("src.lib.source.adapters.ecb.urlopen", fake_urlopen)

    result = EcbAdapter().fetch_series(
        get_series_definition("eu_policy_rate"),
        FetchOptions(start_date="2026-01-01"),
    )

    assert result.ok is True
    assert result.error is None
    assert result.series is not None
    assert result.series.key == "eu_policy_rate"
    assert result.series.provider == "ecb"
    assert result.series.series_id == "FM.D.U2.EUR.4F.KR.DFR.LEV"
    assert result.series.observations[0].date == "2026-03"
    assert result.series.observations[0].value == "2.20"
