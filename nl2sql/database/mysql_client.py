from __future__ import annotations

import mysql.connector
from mysql.connector import Error

from ..config import load_config, require_mysql_config

_CONNECTION: mysql.connector.MySQLConnection | None = None


def get_mysql_connection() -> mysql.connector.MySQLConnection:
    global _CONNECTION
    config = load_config()
    host, port, user, password, database = require_mysql_config(config)

    if _CONNECTION is None or not _CONNECTION.is_connected():
        _CONNECTION = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True,
        )
    else:
        try:
            _CONNECTION.ping(reconnect=True, attempts=1, delay=0)
        except Error:
            _CONNECTION = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                autocommit=True,
            )
    return _CONNECTION
