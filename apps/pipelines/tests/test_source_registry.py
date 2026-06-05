from src.lib.source.registry import SERIES_REGISTRY, get_series_definition


def test_series_registry_contains_taylor_rule_v1_keys():
    expected_keys = {
        "us_policy_rate",
        "us_cpi_headline",
        "us_cpi_core",
        "us_market_real_rate",
        "us_real_gdp",
        "us_output_gap",
        "eu_policy_rate",
        "eu_hicp_headline",
        "eu_hicp_core",
        "eu_market_real_rate",
        "eu_real_gdp",
        "eu_output_gap",
    }

    assert expected_keys.issubset(SERIES_REGISTRY.keys())


def test_series_registry_contains_currency_analysis_v1_keys():
    expected_keys = {
        "eurusd_spot_daily",
        "eurusd_spot_monthly",
        "us_cpi_index",
        "ea_cpi_index",
        "usd_3m_rate",
        "usd_6m_rate",
        "usd_12m_rate",
        "eur_3m_rate",
        "eur_6m_rate",
        "eur_12m_rate",
    }

    assert expected_keys.issubset(SERIES_REGISTRY.keys())


def test_series_registry_entries_include_required_metadata():
    us_policy_rate = get_series_definition("us_policy_rate")
    eu_hicp_headline = get_series_definition("eu_hicp_headline")
    us_core_cpi = get_series_definition("us_cpi_core")
    eu_market_real_rate = get_series_definition("eu_market_real_rate")
    eu_policy_rate = get_series_definition("eu_policy_rate")
    us_market_real_rate = get_series_definition("us_market_real_rate")
    us_output_gap = get_series_definition("us_output_gap")
    eu_output_gap = get_series_definition("eu_output_gap")

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

    assert us_output_gap.provider == "dbnomics"
    assert us_output_gap.external_series_id == "USA.1.0.0.0.AVGDGP"
    assert us_output_gap.unit == "percent"
    assert us_output_gap.source_url == "https://db.nomics.world/AMECO/AVGDGP/USA.1.0.0.0.AVGDGP"
    assert us_output_gap.fallback_external_series_id == "USALORSGPRTSTSAM"

    assert eu_output_gap.provider == "dbnomics"
    assert eu_output_gap.external_series_id == "EA20.1.0.0.0.AVGDGP"
    assert eu_output_gap.unit == "percent"
    assert eu_output_gap.source_url == "https://db.nomics.world/AMECO/AVGDGP/EA20.1.0.0.0.AVGDGP"
    assert eu_output_gap.fallback_external_series_id == "EA19LORSGPRTSTSAM"


def test_currency_analysis_registry_entries_include_required_metadata():
    eurusd_spot_daily = get_series_definition("eurusd_spot_daily")
    eurusd_spot_monthly = get_series_definition("eurusd_spot_monthly")
    us_cpi_index = get_series_definition("us_cpi_index")
    ea_cpi_index = get_series_definition("ea_cpi_index")
    usd_3m_rate = get_series_definition("usd_3m_rate")
    usd_6m_rate = get_series_definition("usd_6m_rate")
    usd_12m_rate = get_series_definition("usd_12m_rate")
    eur_3m_rate = get_series_definition("eur_3m_rate")
    eur_6m_rate = get_series_definition("eur_6m_rate")
    eur_12m_rate = get_series_definition("eur_12m_rate")

    assert eurusd_spot_daily.provider == "ecb"
    assert eurusd_spot_daily.external_series_id == "EXR.D.USD.EUR.SP00.A"
    assert eurusd_spot_daily.region == "FX"
    assert eurusd_spot_daily.frequency == "daily"
    assert eurusd_spot_daily.unit == "usd_per_eur"
    assert eurusd_spot_daily.source_url == "https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A"

    assert eurusd_spot_monthly.provider == "ecb"
    assert eurusd_spot_monthly.external_series_id == "EXR.M.USD.EUR.SP00.A"
    assert eurusd_spot_monthly.frequency == "monthly"
    assert eurusd_spot_monthly.unit == "usd_per_eur"
    assert eurusd_spot_monthly.source_url == "https://data.ecb.europa.eu/data/datasets/EXR/EXR.M.USD.EUR.SP00.A"

    assert us_cpi_index.provider == "fred"
    assert us_cpi_index.external_series_id == "CPIAUCSL"
    assert us_cpi_index.unit == "index"

    assert ea_cpi_index.provider == "fred"
    assert ea_cpi_index.external_series_id == "CP00MI15EA20M086NEST"
    assert ea_cpi_index.frequency == "monthly"
    assert ea_cpi_index.unit == "index"

    assert usd_3m_rate.provider == "fred"
    assert usd_3m_rate.external_series_id == "DTB3"
    assert usd_3m_rate.unit == "percent"

    assert usd_6m_rate.provider == "fred"
    assert usd_6m_rate.external_series_id == "DTB6"
    assert usd_6m_rate.unit == "percent"

    assert usd_12m_rate.provider == "fred"
    assert usd_12m_rate.external_series_id == "DTB1YR"
    assert usd_12m_rate.unit == "percent"

    assert eur_3m_rate.provider == "ecb"
    assert eur_3m_rate.external_series_id == "EST.B.EU000A2QQF32.CR"
    assert eur_3m_rate.unit == "percent"

    assert eur_6m_rate.provider == "ecb"
    assert eur_6m_rate.external_series_id == "EST.B.EU000A2QQF40.CR"
    assert eur_6m_rate.unit == "percent"

    assert eur_12m_rate.provider == "ecb"
    assert eur_12m_rate.external_series_id == "EST.B.EU000A2QQF57.CR"
    assert eur_12m_rate.unit == "percent"


def test_currency_analysis_forward_series_are_not_registered_without_a_real_source_path():
    unexpected_forward_keys = {
        "eurusd_forward_3m",
        "eurusd_forward_6m",
        "eurusd_forward_12m",
    }

    assert unexpected_forward_keys.isdisjoint(SERIES_REGISTRY.keys())
