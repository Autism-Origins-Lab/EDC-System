import sqlite3

VERSION = 5
NAME = "add telephone screening comments"


def upgrade(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(telephone_screenings)")
    }
    if "eligibility_comment" not in columns:
        connection.execute(
            "ALTER TABLE telephone_screenings ADD COLUMN eligibility_comment TEXT"
        )
