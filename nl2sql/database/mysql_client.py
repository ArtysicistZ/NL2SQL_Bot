from __future__ import annotations

import os

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection

from ..config import load_config, require_mysql_config

_POOL: MySQLConnectionPool | None = None


def _build_pool() -> MySQLConnectionPool:
    config = load_config()
    host, port, user, password, database = require_mysql_config(config)
    try:
        pool_size = int(os.getenv("MYSQL_POOL_SIZE", "5"))
    except ValueError:
        pool_size = 5
    return MySQLConnectionPool(
        pool_name="nl2sql_pool",
        pool_size=pool_size,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        autocommit=True,
    )


def get_mysql_connection() -> PooledMySQLConnection:
    """Borrow a connection from the pool.

    Callers MUST ``close()`` the returned connection when done; for a pooled
    connection ``close()`` returns it to the pool rather than disconnecting.
    A pool (instead of a shared singleton) keeps concurrent ``/run_sql`` calls,
    which Starlette runs in its threadpool, from corrupting one shared socket.
    """
    global _POOL
    if _POOL is None:
        _POOL = _build_pool()
    connection = _POOL.get_connection()
    # Reconnect a stale pooled socket (e.g. after the server dropped an idle one).
    if not connection.is_connected():
        connection.reconnect(attempts=2, delay=1)
    return connection
