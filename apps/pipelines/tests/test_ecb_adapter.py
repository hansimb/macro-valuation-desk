import csv
import io
from urllib.error import HTTPError

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
        assert "service/data/FM/FM.D.U2.EUR.4F.KR.DFR.LEV" in request.full_url
        assert "startPeriod=2026-01-01" in request.full_url
        assert request.headers["User-agent"].startswith("macro-valuation-desk/")
        assert request.headers["Accept"] == "text/csv,application/vnd.ecb.data+csv;version=1.0.0"
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


def test_ecb_adapter_normalizes_monthly_start_period(monkeypatch):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["TIME_PERIOD", "OBS_VALUE"])
    writer.writeheader()
    writer.writerow({"TIME_PERIOD": "2026-03", "OBS_VALUE": "2.20"})

    def fake_urlopen(request):
        assert "startPeriod=2026-01" in request.full_url
        assert "startPeriod=2026-01-01" not in request.full_url
        return _FakeResponse(output.getvalue().encode("utf-8"))

    monkeypatch.setattr("src.lib.source.adapters.ecb.urlopen", fake_urlopen)

    result = EcbAdapter().fetch_series(
        get_series_definition("eu_hicp_headline"),
        FetchOptions(start_date="2026-01-01"),
    )

    assert result.ok is True


def test_ecb_adapter_normalizes_quarterly_start_period(monkeypatch):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["TIME_PERIOD", "OBS_VALUE"])
    writer.writeheader()
    writer.writerow({"TIME_PERIOD": "2026-Q1", "OBS_VALUE": "12000"})

    def fake_urlopen(request):
        assert "startPeriod=2026-Q1" in request.full_url
        assert "startPeriod=2026-01-01" not in request.full_url
        return _FakeResponse(output.getvalue().encode("utf-8"))

    monkeypatch.setattr("src.lib.source.adapters.ecb.urlopen", fake_urlopen)

    result = EcbAdapter().fetch_series(
        get_series_definition("eu_real_gdp"),
        FetchOptions(start_date="2026-01-01"),
    )

    assert result.ok is True


def test_ecb_adapter_includes_request_url_and_response_body_in_http_errors(monkeypatch):
    def fake_urlopen(request):
        raise HTTPError(
            url=request.full_url,
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(b'{"detail":"invalid ECB request"}'),
        )

    monkeypatch.setattr("src.lib.source.adapters.ecb.urlopen", fake_urlopen)

    result = EcbAdapter().fetch_series(
        get_series_definition("eu_policy_rate"),
        FetchOptions(),
    )

    assert result.ok is False
    assert result.error is not None
    assert "service/data/FM/FM.D.U2.EUR.4F.KR.DFR.LEV" in result.error.message
    assert "invalid ECB request" in result.error.message


def test_ecb_adapter_summarizes_html_block_pages(monkeypatch):
    html = """
    <html><head><title>European Central Bank</title></head>
    <body>
      <h1>ECB Data Portal<br> <br> Your access has been blocked due to security concerns. <br></h1>
      <p class="signature">HTTP status code: 400</p>
    </body></html>
    """.encode("utf-8")

    def fake_urlopen(request):
        raise HTTPError(
            url=request.full_url,
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(html),
        )

    monkeypatch.setattr("src.lib.source.adapters.ecb.urlopen", fake_urlopen)

    result = EcbAdapter().fetch_series(
        get_series_definition("eu_policy_rate"),
        FetchOptions(),
    )

    assert result.ok is False
    assert result.error is not None
    assert "Your access has been blocked due to security concerns." in result.error.message
    assert "<html" not in result.error.message
