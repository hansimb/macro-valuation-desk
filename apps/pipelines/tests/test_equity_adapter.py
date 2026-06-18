import json

from src.lib.source.adapters.equity import build_sp500_constituent_snapshot_rows


WIKIPEDIA_HTML = """
<table class="wikitable sortable">
<tr>
  <th>Symbol</th><th>Security</th><th>GICS Sector</th><th>GICS Sub-Industry</th>
  <th>Headquarters Location</th><th>Date added</th><th>CIK</th><th>Founded</th>
</tr>
<tr>
  <td><a>AAPL</a></td><td><a>Apple Inc.</a></td><td>Information Technology</td><td>Technology Hardware</td>
  <td>Cupertino, California</td><td>1982-11-30</td><td>0000320193</td><td>1977</td>
</tr>
<tr>
  <td><a>ACN</a></td><td><a>Accenture</a></td><td>Information Technology</td><td>IT Consulting</td>
  <td>Dublin, Ireland</td><td>2011-07-06</td><td>0001467373</td><td>1989</td>
</tr>
</table>
"""


def _companyfacts(revenue: int, shares: int) -> str:
    return json.dumps(
        {
            "facts": {
                "dei": {
                    "EntityCommonStockSharesOutstanding": {
                        "units": {
                            "shares": [
                                {
                                    "end": "2026-04-01",
                                    "val": shares,
                                    "form": "10-Q",
                                    "filed": "2026-05-01",
                                }
                            ]
                        }
                    }
                },
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {
                                    "start": "2025-01-01",
                                    "end": "2025-12-31",
                                    "val": revenue,
                                    "form": "10-K",
                                    "filed": "2026-02-01",
                                }
                            ]
                        }
                    }
                },
            }
        }
    )


def _chart(close: float, volume: int) -> str:
    return json.dumps(
        {
            "chart": {
                "result": [
                    {
                        "timestamp": [1781703000, 1781789400],
                        "indicators": {
                            "quote": [
                                {
                                    "close": [close - 1, close],
                                    "volume": [volume, volume],
                                }
                            ]
                        },
                    }
                ],
                "error": None,
            }
        }
    )


def test_build_sp500_constituent_snapshot_rows_combines_wikipedia_sec_and_yahoo_chart_data():
    payloads = {
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies": WIKIPEDIA_HTML,
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json": _companyfacts(
            revenue=400_000_000_000,
            shares=15_000_000_000,
        ),
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=3mo&interval=1d": _chart(
            close=200.0,
            volume=50_000_000,
        ),
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0001467373.json": _companyfacts(
            revenue=80_000_000_000,
            shares=600_000_000,
        ),
        "https://query1.finance.yahoo.com/v8/finance/chart/ACN?range=3mo&interval=1d": _chart(
            close=300.0,
            volume=2_000_000,
        ),
    }

    rows = build_sp500_constituent_snapshot_rows(
        fetch_text=lambda url, _headers=None: payloads[url],
        as_of_date="2026-06-18",
    )

    assert rows == [
        {
            "universe_key": "sp500",
            "as_of_date": "2026-06-18",
            "ticker": "AAPL",
            "company": "Apple Inc.",
            "country_code": "US",
            "country_name": "United States",
            "sector": "Information Technology",
            "market_cap": 3_000_000_000_000.0,
            "trailing_12m_revenue": 400_000_000_000,
            "ps_ratio": 7.5,
            "index_weight_pct": 94.34,
            "average_daily_traded_value": 9_975_000_000.0,
            "source_provider": "wikipedia+sec+yahoo-chart",
            "source_url": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        },
        {
            "universe_key": "sp500",
            "as_of_date": "2026-06-18",
            "ticker": "ACN",
            "company": "Accenture",
            "country_code": "IE",
            "country_name": "Ireland",
            "sector": "Information Technology",
            "market_cap": 180_000_000_000.0,
            "trailing_12m_revenue": 80_000_000_000,
            "ps_ratio": 2.25,
            "index_weight_pct": 5.66,
            "average_daily_traded_value": 599_000_000.0,
            "source_provider": "wikipedia+sec+yahoo-chart",
            "source_url": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        },
    ]
