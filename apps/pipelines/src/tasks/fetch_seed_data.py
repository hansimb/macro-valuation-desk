from prefect import task


@task
def fetch_seed_data() -> list[dict[str, str]]:
    return [
        {"series": "cpi_yoy", "value": "2.9", "as_of": "2026-05-01"},
        {"series": "fed_funds_upper", "value": "5.50", "as_of": "2026-05-01"},
    ]
