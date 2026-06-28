from __future__ import annotations

import sys
from urllib.parse import urlparse

from . import connection as _connection
from .checkpoints import (
    build_fetch_options_for_series,
    build_fetch_options_from_checkpoint,
    read_latest_checkpoint,
    record_pipeline_run,
    utc_now_iso,
    write_successful_checkpoint,
)
from .currency_analysis import (
    replace_currency_data_availability,
    replace_currency_irp_snapshots,
    replace_currency_ppp_paths,
    replace_currency_ppp_snapshots,
)
from .highest_ps_ranking import (
    read_highest_ps_candidate_rows,
    replace_highest_ps_section_rankings,
    replace_highest_ps_section_summaries,
    upsert_equity_index_constituent_snapshots,
)
from .macro_reference import replace_macro_reference_metrics
from .schema import (
    _schema_sql,
    bootstrap_taylor_rule_schema,
    read_staging_rows_for_series,
    upsert_raw_observations,
    upsert_series_metadata,
    upsert_staging_observations,
)
from .taylor_rule import replace_taylor_rule_inputs

psycopg = _connection.psycopg
dict_row = _connection.dict_row
get_database_url = _connection.get_database_url

DEFAULT_CONNECT_TIMEOUT_SECONDS = 2


def _database_target(database_url: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.hostname:
        return "configured DATABASE_URL"

    target = parsed.hostname
    if parsed.port:
        target = f"{target}:{parsed.port}"
    if parsed.path and parsed.path != "/":
        target = f"{target}{parsed.path}"

    return target


def get_connection():
    database_url = get_database_url()
    if not database_url:
        return None

    target = _database_target(database_url)
    print(f"Connecting to Postgres at {target}...", file=sys.stderr, flush=True)

    try:
        return psycopg.connect(
            database_url,
            row_factory=dict_row,
            connect_timeout=DEFAULT_CONNECT_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        message = (
            f"Cannot connect to Postgres at {target}. "
            "Is the Docker DB running? Try `npm run dev:db` before running the pipeline. "
            f"Original error: {exc}"
        )
        print(message, file=sys.stderr, flush=True)
        raise RuntimeError(message) from exc


__all__ = [
    "_schema_sql",
    "bootstrap_taylor_rule_schema",
    "build_fetch_options_for_series",
    "build_fetch_options_from_checkpoint",
    "dict_row",
    "get_connection",
    "get_database_url",
    "psycopg",
    "read_highest_ps_candidate_rows",
    "read_latest_checkpoint",
    "read_staging_rows_for_series",
    "record_pipeline_run",
    "replace_currency_data_availability",
    "replace_currency_irp_snapshots",
    "replace_currency_ppp_paths",
    "replace_currency_ppp_snapshots",
    "replace_highest_ps_section_rankings",
    "replace_highest_ps_section_summaries",
    "replace_macro_reference_metrics",
    "replace_taylor_rule_inputs",
    "upsert_equity_index_constituent_snapshots",
    "upsert_raw_observations",
    "upsert_series_metadata",
    "upsert_staging_observations",
    "utc_now_iso",
    "write_successful_checkpoint",
]
