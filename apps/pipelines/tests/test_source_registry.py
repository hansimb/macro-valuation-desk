from src.lib.source.registry import SERIES_REGISTRY, get_series_definition


def test_series_registry_contains_taylor_rule_v1_keys():
    expected_keys = {
        "us_policy_rate",
        "us_cpi_headline",
        "eu_policy_rate",
        "eu_hicp_headline",
    }

    assert expected_keys.issubset(SERIES_REGISTRY.keys())


def test_series_registry_entries_include_required_metadata():
    us_policy_rate = get_series_definition("us_policy_rate")
    eu_hicp_headline = get_series_definition("eu_hicp_headline")

    assert us_policy_rate.provider == "fred"
    assert us_policy_rate.external_series_id == "DFEDTARU"
    assert us_policy_rate.region == "US"
    assert us_policy_rate.frequency == "daily"
    assert us_policy_rate.source_url == "https://fred.stlouisfed.org/series/DFEDTARU"

    assert eu_hicp_headline.provider == "ecb"
    assert eu_hicp_headline.external_series_id == "HICP.M.U2.N.000000.4D0.ANR"
    assert eu_hicp_headline.region == "EU"
    assert eu_hicp_headline.frequency == "monthly"
    assert eu_hicp_headline.source_url == (
        "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR"
    )
