import logging
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock

from app import config

_transaction_connection: ContextVar[sqlite3.Connection | None] = ContextVar(
    "transaction_connection", default=None
)
_database_lock = RLock()
_connection_depth: ContextVar[int] = ContextVar("connection_depth", default=0)
_commit_listener: Callable[[], None] | None = None


def set_commit_listener(listener: Callable[[], None] | None) -> None:
    global _commit_listener
    _commit_listener = listener


@contextmanager
def database_maintenance() -> Iterator[None]:
    """Exclude application connections while backing up or restoring database files."""
    with _database_lock:
        if _connection_depth.get():
            raise RuntimeError(
                "Finish the current database operation before maintenance."
            )
        yield


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open a managed connection, or join an explicitly scoped transaction."""
    active_connection = _transaction_connection.get()
    if active_connection is not None:
        yield active_connection
        return

    with _database_lock:
        config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(config.DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        token = _connection_depth.set(_connection_depth.get() + 1)
        try:
            yield connection
            changed = connection.in_transaction and connection.total_changes > 0
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
            _connection_depth.reset(token)
        # A backup error must never turn an already committed save into a save error.
        if changed and _commit_listener is not None:
            try:
                _commit_listener()
            except Exception:
                logging.getLogger(__name__).exception(
                    "Post-save backup notification failed"
                )


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Commit repository calls together; nested scopes join the outer transaction."""
    active_connection = _transaction_connection.get()
    if active_connection is not None:
        yield active_connection
        return

    with get_connection() as connection:
        # Acquire the write lock before reading the status to avoid a stale decision.
        connection.execute("BEGIN IMMEDIATE")
        token = _transaction_connection.set(connection)
        try:
            yield connection
        finally:
            _transaction_connection.reset(token)
