from __future__ import annotations

from prefect import task

from src.lib.db import (
    bootstrap_taylor_rule_schema,
    replace_highest_ps_section_rankings,
    replace_highest_ps_section_summaries,
)
from src.lib.pipeline.checkpoints import record_pipeline_run, utc_now_iso


@task
def load_highest_ps_ranking_layers(
    connection,
    *,
    section_summary_rows: list[dict[str, object]],
    section_ranking_rows: list[dict[str, object]],
) -> dict[str, int]:
    run_at = utc_now_iso()
    record_pipeline_run(
        connection,
        run_id=f"highest-ps-ranking-{run_at}",
        domain_key="highest_ps_ranking",
        started_at=run_at,
        finished_at=None,
        status="running",
        error_summary=None,
    )

    if connection is not None:
        bootstrap_taylor_rule_schema(connection)
        replace_highest_ps_section_summaries(connection, section_summary_rows)
        replace_highest_ps_section_rankings(connection, section_ranking_rows)

    record_pipeline_run(
        connection,
        run_id=f"highest-ps-ranking-{run_at}",
        domain_key="highest_ps_ranking",
        started_at=run_at,
        finished_at=run_at,
        status="success",
        error_summary=None,
    )

    return {
        "section_summary_rows": len(section_summary_rows),
        "ranking_rows": len(section_ranking_rows),
    }
