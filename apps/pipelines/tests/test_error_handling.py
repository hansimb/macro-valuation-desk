from src.lib.pipeline.error_handling import (
    collect_fetch_errors,
    format_flow_errors,
    raise_on_failed_flow,
)
from src.lib.source.types import FetchResult


def test_collect_fetch_errors_formats_key_and_message_pairs():
    fetch_results = [
        FetchResult.failure(
            provider="ecb",
            key="eur_3m_rate",
            external_series_id="EST.B.EU000A2QQF32.CR",
            error_type="fetch_error",
            message="blocked",
        ),
        FetchResult.failure(
            provider="fred",
            key="usd_3m_rate",
            external_series_id="DTB3",
            error_type="fetch_error",
            message="timeout",
        ),
    ]

    assert collect_fetch_errors(fetch_results) == [
        "eur_3m_rate: blocked",
        "usd_3m_rate: timeout",
    ]


def test_format_flow_errors_renders_bulleted_lines():
    assert format_flow_errors("currency_analysis", ["eur_3m_rate: blocked", "eur_6m_rate: blocked"]) == (
        "currency_analysis flow failed:\n"
        "  - eur_3m_rate: blocked\n"
        "  - eur_6m_rate: blocked"
    )


def test_raise_on_failed_flow_uses_standardized_error_format():
    try:
        raise_on_failed_flow("taylor_rule", {"status": "failed", "errors": ["us_policy_rate: boom"]})
    except RuntimeError as error:
        assert str(error) == "taylor_rule flow failed:\n  - us_policy_rate: boom"
    else:
        raise AssertionError("expected raise_on_failed_flow() to raise for failed child flow")
