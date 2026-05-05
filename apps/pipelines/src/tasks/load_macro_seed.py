from prefect import task

from src.lib.db import get_connection


@task
def load_macro_seed(rows: list[dict[str, str]]) -> dict[str, int]:
    connection = get_connection()

    if connection is None:
        return {"rows_loaded": len(rows)}

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                create table if not exists raw.macro_series (
                    series text not null,
                    value numeric not null,
                    as_of date not null
                )
                """
            )
            cursor.executemany(
                """
                insert into raw.macro_series (series, value, as_of)
                values (%(series)s, %(value)s, %(as_of)s)
                """,
                rows,
            )

    return {"rows_loaded": len(rows)}
