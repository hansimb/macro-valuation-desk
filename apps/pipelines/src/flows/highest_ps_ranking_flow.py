from __future__ import annotations

from prefect import flow

from src.lib.db import bootstrap_taylor_rule_schema, get_connection, read_highest_ps_candidate_rows
from src.lib.pipeline.transforms.highest_ps_ranking import build_highest_ps_outputs
from src.tasks import load_highest_ps_ranking_layers as load_highest_ps_ranking_layers_module


def _call_task(task_or_fn, *args, **kwargs):
    if hasattr(task_or_fn, "fn"):
        return task_or_fn.fn(*args, **kwargs)

    return task_or_fn(*args, **kwargs)


def run_highest_ps_ranking_flow() -> dict[str, object]:
    connection = get_connection()
    if connection is not None:
        bootstrap_taylor_rule_schema(connection)

    candidate_rows = read_highest_ps_candidate_rows(connection)
    outputs = build_highest_ps_outputs(candidate_rows)

    if not outputs["sections"]:
        section_summary_rows = [
            {
                "section_key": "usa",
                "as_of_date": None,
                "universe_key": "sp500",
                "universe_label": "S&P 500",
                "section_label": "USA High P/S Leaders",
                "benchmark_key": "sp500",
                "benchmark_label": "S&P 500 Average P/S",
                "average_ps_ratio": None,
                "top_basket_average_ps_ratio": None,
                "top_basket_index_weight_pct": None,
                "eligible_constituent_count": 0,
                "unavailable": True,
            }
        ]
        load_summary = _call_task(
            load_highest_ps_ranking_layers_module.load_highest_ps_ranking_layers,
            connection,
            section_summary_rows=section_summary_rows,
            section_ranking_rows=[],
        )
        return {
            "status": "unavailable",
            "section_count": 1,
            "ranking_row_count": 0,
            "load_summary": load_summary,
        }

    section_summary_rows = [
        {
            "section_key": section["key"],
            "as_of_date": section["as_of_date"],
            "universe_key": section["universe_key"],
            "universe_label": section["universe_label"],
            "section_label": section["label"],
            "benchmark_key": section["benchmark"]["key"],
            "benchmark_label": section["benchmark"]["label"],
            "average_ps_ratio": section["benchmark"]["average_ps_ratio"],
            "top_basket_average_ps_ratio": section["benchmark"]["top_basket_average_ps_ratio"],
            "top_basket_index_weight_pct": section["benchmark"]["top_basket_index_weight_pct"],
            "eligible_constituent_count": section["benchmark"]["eligible_constituent_count"],
            "unavailable": section["unavailable"],
        }
        for section in outputs["sections"]
    ]
    section_ranking_rows = [
        {
            "section_key": section["key"],
            **row,
        }
        for section in outputs["sections"]
        for row in section["ranking"]
    ]

    load_summary = _call_task(
        load_highest_ps_ranking_layers_module.load_highest_ps_ranking_layers,
        connection,
        section_summary_rows=section_summary_rows,
        section_ranking_rows=section_ranking_rows,
    )

    return {
        "status": "success",
        "section_count": len(outputs["sections"]),
        "ranking_row_count": len(section_ranking_rows),
        "load_summary": load_summary,
    }


@flow(name="highest-ps-ranking-flow")
def highest_ps_ranking_flow() -> dict[str, object]:
    return run_highest_ps_ranking_flow()


if __name__ == "__main__":
    highest_ps_ranking_flow()
