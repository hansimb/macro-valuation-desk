from urllib.error import URLError

from src.lib.source.adapters.issuer_pages import (
    IssuerPagesAdapter,
    parse_ishares_snapshot,
    parse_ishares_url_from_product_list,
    parse_spdr_snapshot,
)


class _FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_parse_ishares_url_from_product_list_finds_ticker_link():
    html = """
    <tr>
      <td class="links"><a href="/us/products/239650/ishares-msci-germany-etf">EWG</a></td>
      <td class="links"><a href="/us/products/239650/ishares-msci-germany-etf">iShares MSCI Germany ETF</a></td>
    </tr>
    """

    assert parse_ishares_url_from_product_list(html, "EWG") == (
        "https://www.ishares.com/us/products/239650/ishares-msci-germany-etf"
    )


def test_parse_ishares_snapshot_reads_embedded_fundamentals():
    html = """
    "priceBook":{"visible":true,"label":"P/B Ratio","formattedValue":"2.10","formattedAsOfDate":"Jul 14, 2026"},
    "priceEarnings":{"visible":true,"label":"P/E Ratio","formattedValue":"18.32","formattedAsOfDate":"Jul 14, 2026"},
    "twelveMonTrlYld":{"visible":true,"formattedValue":"2.14","formattedAsOfDate":"Jul 14, 2026"}
    """

    snapshot = parse_ishares_snapshot(
        html,
        symbol="EWG",
        source_url="https://www.ishares.com/us/products/239650/ishares-msci-germany-etf",
    )

    assert snapshot.provider == "issuer_pages"
    assert snapshot.symbol == "EWG"
    assert snapshot.trailing_pe == 18.32
    assert snapshot.price_to_book == 2.10
    assert snapshot.dividend_yield_pct == 2.14
    assert snapshot.as_of == "2026-07-14"


def test_parse_ishares_snapshot_reads_html_escaped_embedded_fundamentals():
    html = """
    &quot;priceBook&quot;:{&quot;formattedValue&quot;:&quot;1.91&quot;,&quot;formattedAsOfDate&quot;:&quot;Jul 14, 2026&quot;},
    &quot;priceEarnings&quot;:{&quot;formattedValue&quot;:&quot;17.91&quot;,&quot;formattedAsOfDate&quot;:&quot;Jul 14, 2026&quot;}
    """

    snapshot = parse_ishares_snapshot(
        html,
        symbol="EWG",
        source_url="https://www.ishares.com/us/products/239650/ishares-msci-germany-etf",
    )

    assert snapshot.trailing_pe == 17.91
    assert snapshot.price_to_book == 1.91
    assert snapshot.as_of == "2026-07-14"


def test_parse_spdr_snapshot_reads_key_value_table():
    html = """
    <th class="label" scope="row">Price/Book Ratio</th><td class="data">5.44</td>
    <th class="label" scope="row">Price/Earnings Ratio FY1</th><td class="data">22.64</td>
    <th class="label" scope="row">Index Dividend Yield</th><td class="data">1.12%</td>
    """

    snapshot = parse_spdr_snapshot(
        html,
        symbol="SPY",
        source_url="https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy",
    )

    assert snapshot.provider == "issuer_pages"
    assert snapshot.symbol == "SPY"
    assert snapshot.trailing_pe is None
    assert "issuer_page.trailingPe_unavailable_FY1_is_forward" in snapshot.missing_fields
    assert snapshot.price_to_book == 5.44
    assert snapshot.dividend_yield_pct == 1.12


def test_issuer_pages_adapter_fetches_ishares_without_api_token():
    product_list_html = """
    <td class="links"><a href="/us/products/239650/ishares-msci-germany-etf">EWG</a></td>
    """
    product_html = """
    "priceBook":{"formattedValue":"2.10","formattedAsOfDate":"Jul 14, 2026"},
    "priceEarnings":{"formattedValue":"18.32","formattedAsOfDate":"Jul 14, 2026"}
    """

    def fake_opener(request):
        if "etf-investments" in request.full_url:
            return _FakeResponse(product_list_html.encode("utf-8"))
        assert request.full_url == "https://www.ishares.com/us/products/239650/ishares-msci-germany-etf"
        return _FakeResponse(product_html.encode("utf-8"))

    result = IssuerPagesAdapter(opener=fake_opener).fetch_fundamentals_snapshot("EWG.US")

    assert result.ok is True
    assert result.snapshot is not None
    assert result.snapshot.trailing_pe == 18.32


def test_spdr_reads_index_cash_flow_proxy_without_claiming_exact_fcf():
    page = """
    <tr><th>Price/Earnings Ratio FY1</th><td class="data">20.97</td></tr>
    <tr><th>Price/Cash Flow</th><td class="data">18.02</td></tr>
    <tr><th>Price/Earnings</th><td class="data">24.69</td></tr>
    """
    snapshot = parse_spdr_snapshot(page, symbol="SPY", source_url="https://www.ssga.com/spy")
    assert snapshot.price_to_cash_flow == 18.02
    assert snapshot.price_to_cash_flow_method == "issuer_index_price_to_cash_flow_proxy"
    assert snapshot.price_to_free_cash_flow is None
    assert snapshot.trailing_pe is None
    assert "issuer_page.priceToCashFlow" not in snapshot.missing_fields


def test_spdr_missing_cash_flow_does_not_consume_next_rows_number():
    page = """
    <tr><th>Price/Cash Flow</th><td class="data">-</td></tr>
    <tr><th>Price/Book Ratio</th><td class="data">5.25</td></tr>
    """
    snapshot = parse_spdr_snapshot(page, symbol="SPY", source_url="https://www.ssga.com/spy")
    assert snapshot.price_to_cash_flow is None
    assert snapshot.price_to_cash_flow_method == "provider_price_to_cash_flow_unavailable"


def test_ishares_reads_current_twelve_month_trailing_yield_field():
    page = '\"twelveMonTrlYld\":{\"formattedValue\":\"1.88%\",\"formattedAsOfDate\":\"Aug 31, 2026\"}'
    snapshot = parse_ishares_snapshot(page, symbol="EWG", source_url="https://www.ishares.com/ewg")
    assert snapshot.dividend_yield_pct == 1.88
    assert snapshot.as_of == "2026-08-31"


def test_spdr_uses_index_characteristics_date_over_http_modification_date():
    page = """
    <section><h2>Fund Characteristics <span class="date">as of Sep 11 2026</span></h2></section>
    <section><h2>Index Characteristics <span class="date">as of Sep 10 2026</span></h2>
    <tr><th>Price/Cash Flow</th><td class="data">18.02</td></tr></section>
    """
    snapshot = parse_spdr_snapshot(page, symbol="SPY", source_url="https://www.ssga.com/spy", as_of="2026-09-12")
    assert snapshot.as_of == "2026-09-10"


def test_ishares_does_not_substitute_a_different_distribution_yield_basis():
    page = '\"distributionYield\":{\"formattedValue\":\"3.5\",\"formattedAsOfDate\":\"Sep 10, 2026\"}'
    snapshot = parse_ishares_snapshot(page, symbol="EWG", source_url="https://www.ishares.com/ewg")
    assert snapshot.dividend_yield_pct is None


def test_issuer_pages_adapter_retries_a_transient_product_page_timeout():
    product_list_html = '<a href="/us/products/239650/ishares-msci-germany-etf">EWG</a>'
    product_html = '"priceEarnings":{"formattedValue":"18.32","formattedAsOfDate":"Sep 10, 2026"}'
    product_attempts = 0

    def fake_opener(request):
        nonlocal product_attempts
        if "etf-investments" in request.full_url:
            return _FakeResponse(product_list_html.encode())
        product_attempts += 1
        if product_attempts == 1:
            raise URLError(TimeoutError("timed out"))
        return _FakeResponse(product_html.encode())

    result = IssuerPagesAdapter(opener=fake_opener, retry_delay_seconds=0).fetch_fundamentals_snapshot("EWG.US")

    assert result.ok is True
    assert product_attempts == 2


def test_issuer_pages_adapter_reuses_the_ishares_product_list():
    product_list_html = """
    <a href="/us/products/239650/ishares-msci-germany-etf">EWG</a>
    <a href="/us/products/239649/ishares-msci-france-etf">EWQ</a>
    """
    product_html = '"priceBook":{"formattedValue":"2.10","formattedAsOfDate":"Sep 10, 2026"}'
    product_list_requests = 0

    def fake_opener(request):
        nonlocal product_list_requests
        if "etf-investments" in request.full_url:
            product_list_requests += 1
            return _FakeResponse(product_list_html.encode())
        return _FakeResponse(product_html.encode())

    adapter = IssuerPagesAdapter(opener=fake_opener)
    assert adapter.fetch_fundamentals_snapshot("EWG.US").ok is True
    assert adapter.fetch_fundamentals_snapshot("EWQ.US").ok is True
    assert product_list_requests == 1
