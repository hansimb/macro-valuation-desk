from __future__ import annotations

import os

import psycopg


def get_database_url() -> str | None:
    return os.getenv("DATABASE_URL")


def get_connection():
    database_url = get_database_url()
    if not database_url:
        return None

    return psycopg.connect(database_url)
