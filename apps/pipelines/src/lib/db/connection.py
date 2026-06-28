from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row

from src.lib.runtime_env import load_project_env


def get_database_url() -> str | None:
    load_project_env()
    return os.getenv("DATABASE_URL", "postgresql://mvd:mvd@localhost:5432/mvd")


def get_connection():
    database_url = get_database_url()
    if not database_url:
        return None

    return psycopg.connect(database_url, row_factory=dict_row)
