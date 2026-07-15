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
    "distributionYield":{"visible":true,"formattedValue":"2.14","formattedAsOfDate":"Jul 14, 2026"}
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
    assert snapshot.trailing_pe == 22.64
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
