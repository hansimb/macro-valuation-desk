from src.lib.source.registry import SERIES_REGISTRY, get_series_definition


def test_series_registry_contains_taylor_rule_v1_keys():
    expected_keys = {
        "us_policy_rate",
        "us_cpi_headline",
        "us_cpi_core",
        "us_market_real_rate",
        "us_real_gdp",
        "eu_policy_rate",
        "eu_hicp_headline",
        "eu_hicp_core",
        "eu_market_real_rate",
        "eu_real_gdp",
    }

    assert expected_keys.issubset(SERIES_REGISTRY.keys())


def test_series_registry_entries_include_required_metadata():
    us_policy_rate = get_series_definition("us_policy_rate")
    eu_hicp_headline = get_series_definition("eu_hicp_headline")
    us_core_cpi = get_series_definition("us_cpi_core")
    eu_market_real_rate = get_series_definition("eu_market_real_rate")
    eu_policy_rate = get_series_definition("eu_policy_rate")
    us_market_real_rate = get_series_definition("us_market_real_rate")

    assert us_policy_rate.provider == "fred"
    assert us_policy_rate.external_series_id == "DFEDTARU"
    assert us_policy_rate.region == "US"
    assert us_policy_rate.frequency == "daily"
    assert us_policy_rate.source_url == "https://fred.stlouisfed.org/series/DFEDTARU"

    assert eu_hicp_headline.provider == "ecb"
    assert eu_hicp_headline.external_series_id == "HICP.M.U2.N.000000.4D0.ANR"
    assert eu_hicp_headline.region == "EU"
    assert eu_hicp_headline.frequency == "monthly"
    assert eu_hicp_headline.source_url == "https://data.ecb.europa.eu/data/datasets/HICP/HICP.M.U2.N.000000.4D0.ANR"
    assert eu_hicp_headline.fallback_provider == "fred"
    assert eu_hicp_headline.fallback_external_series_id == "CP00MI15EA20M086NEST"

    assert us_core_cpi.external_series_id == "CPILFESL"
    assert us_core_cpi.unit == "index"
    assert us_core_cpi.source_url == "https://fred.stlouisfed.org/series/CPILFESL"

    assert eu_policy_rate.provider == "ecb"
    assert eu_policy_rate.external_series_id == "FM.D.U2.EUR.4F.KR.DFR.LEV"
    assert eu_policy_rate.source_url == "https://data.ecb.europa.eu/data/datasets/FM/FM.D.U2.EUR.4F.KR.DFR.LEV"
    assert eu_policy_rate.fallback_provider == "fred"
    assert eu_policy_rate.fallback_external_series_id == "ECBDFR"

    assert us_market_real_rate.provider == "fred"
    assert us_market_real_rate.external_series_id == "DFII10"
    assert us_market_real_rate.source_url == "https://fred.stlouisfed.org/series/DFII10"

    assert eu_market_real_rate.provider == "ecb"
    assert eu_market_real_rate.external_series_id == "FM.M.U2.EUR.4F.BB.U2_10Y.YLD"
    assert eu_market_real_rate.frequency == "monthly"
    assert eu_market_real_rate.source_url == "https://data.ecb.europa.eu/data/datasets/FM/FM.M.U2.EUR.4F.BB.U2_10Y.YLD"
    assert eu_market_real_rate.fallback_external_series_id == "IRLTLT01EZM156N"
