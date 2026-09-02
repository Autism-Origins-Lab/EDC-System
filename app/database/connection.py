import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app import config


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
