"""
Database connection manager.

This module provides the single entry point for accessing the SQLite
database used by the LIMS application.
"""

from pathlib import Path
import sqlite3

from config import DATABASE_FILE


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite connection.

    If the database file does not exist, SQLite will create it
    automatically.

    Uses WAL (Write-Ahead Logging) mode so readers don't block
    writers and vice versa -- important now that the app is meant
    to be deployed as a single shared instance with multiple
    concurrent users. There is still only one writer at a time,
    but WAL keeps that lock window short and lets everyone else
    keep reading meanwhile.

    Returns
    -------
    sqlite3.Connection
        Active database connection.
    """

    # Ensure the database directory exists
    Path(DATABASE_FILE).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_FILE)

    # Return rows as dictionaries instead of tuples
    connection.row_factory = sqlite3.Row

    # WAL persists as a database-level setting after the first call,
    # but it's cheap to set on every connection and guarantees it's
    # always on, even against a fresh/copied database file.
    connection.execute("PRAGMA journal_mode = WAL;")

    # busy_timeout makes a connection wait (instead of failing
    # immediately) if it hits the one active writer -- important
    # with several concurrent users on the shared instance.
    connection.execute("PRAGMA busy_timeout = 5000;")

    return connection