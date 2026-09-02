import sqlite3

from app.database.connection import get_connection
from app.database.schema import SCHEMA_SQL

CURRENT_SCHEMA_VERSION = 1

def get_schema_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])

def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"PRAGMA user_version = {version}")

def run_migrations() -> None:
    with get_connection() as connection:
        version = get_schema_version(connection)

        if version < 1:
            connection.executescript(SCHEMA_SQL)
            set_schema_version(connection, CURRENT_SCHEMA_VERSION)

