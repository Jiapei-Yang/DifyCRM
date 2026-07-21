from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

from .config import get_settings


settings = get_settings()

pool = MySQLConnectionPool(
    pool_name="dify_crm_pool",
    pool_size=5,
    host=settings.mysql_host,
    port=settings.mysql_port,
    user=settings.mysql_user,
    password=settings.mysql_password,
    database=settings.mysql_database,
    charset="utf8mb4",
    autocommit=False,
)


@contextmanager
def get_conn() -> Iterator[Any]:
    conn = pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_conn() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query: str, params: tuple[Any, ...] = ()) -> int:
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        last_id = cursor.lastrowid
        cursor.close()
        return int(last_id or 0)
