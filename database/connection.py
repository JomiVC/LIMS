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

    return connection