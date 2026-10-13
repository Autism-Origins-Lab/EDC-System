import sqlite3

VERSION = 2
NAME = "add patient form status"


def upgrade(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(patients)")
    }
    if "form_status" not in columns:
        connection.execute(
            "ALTER TABLE patients ADD COLUMN form_status TEXT DEFAULT 'Pending'"
        )
