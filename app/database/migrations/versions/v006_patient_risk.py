import sqlite3

VERSION = 6
NAME = "add patient risk"


def upgrade(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(patients)")
    }
    if "risk" not in columns:
        connection.execute("ALTER TABLE patients ADD COLUMN risk BOOLEAN")
