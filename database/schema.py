"""
database/schema.py

LIMS Database Schema

Storage Engine v1.0
"""

from sqlite3 import Connection

from database.connection import get_connection


# ==========================================================
# PUBLIC API
# ==========================================================

def initialize_database() -> None:
    """
    Create every database table.

    Safe to execute multiple times.
    """

    conn = get_connection()

    conn.execute("PRAGMA foreign_keys = ON;")

    create_storage_freezers_table(conn)
    create_storage_racks_table(conn)
    create_storage_boxes_table(conn)
    create_storage_positions_table(conn)
    create_storage_containers_table(conn)

    create_indexes(conn)

    conn.commit()
    conn.close()


# ==========================================================
# STORAGE
# ==========================================================

def create_storage_freezers_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS storage_freezers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL UNIQUE,

            temperature REAL,

            description TEXT

        );
        """
    )


def create_storage_racks_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS storage_racks (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            freezer_id INTEGER NOT NULL,

            rack_name TEXT NOT NULL,

            rack_type TEXT NOT NULL
                CHECK(rack_type IN ('EPPENDORF','FALCON')),

            description TEXT,

            FOREIGN KEY(freezer_id)
                REFERENCES storage_freezers(id)
                ON DELETE CASCADE,

            UNIQUE(freezer_id, rack_name)

        );
        """
    )


def create_storage_boxes_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS storage_boxes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            box_name TEXT NOT NULL UNIQUE,

            legacy_name TEXT,

            box_type TEXT NOT NULL
                CHECK(box_type IN ('EPPENDORF','FALCON')),

            owner TEXT,

            rack_id INTEGER NOT NULL,

            shelf INTEGER,

            slot INTEGER NOT NULL,

            notes TEXT,

            active INTEGER NOT NULL DEFAULT 1
                CHECK(active IN (0,1)),

            FOREIGN KEY(rack_id)
                REFERENCES storage_racks(id)
                ON DELETE RESTRICT

        );
        """
    )


def create_storage_positions_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS storage_positions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            box_id INTEGER NOT NULL,

            position TEXT NOT NULL,

            FOREIGN KEY(box_id)
                REFERENCES storage_boxes(id)
                ON DELETE CASCADE,

            UNIQUE(box_id, position)

        );
        """
    )


def create_storage_containers_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS storage_containers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            container_type TEXT NOT NULL,

            position_id INTEGER NOT NULL UNIQUE,

            label TEXT,

            status TEXT NOT NULL
                DEFAULT 'ACTIVE'
                CHECK(
                    status IN (
                        'ACTIVE',
                        'CONSUMED',
                        'DISCARDED'
                    )
                ),

            created_at TEXT,

            updated_at TEXT,

            notes TEXT,

            FOREIGN KEY(position_id)
                REFERENCES storage_positions(id)
                ON DELETE RESTRICT

        );
        """
    )
# ==========================================================
# INDEXES
# ==========================================================

def create_indexes(conn: Connection) -> None:
    """
    Create indexes to improve query performance.
    """

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_racks_freezer
        ON storage_racks(freezer_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_boxes_rack
        ON storage_boxes(rack_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_positions_box
        ON storage_positions(box_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_containers_position
        ON storage_containers(position_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_boxes_owner
        ON storage_boxes(owner);
    """)


# ==========================================================
# DEVELOPMENT UTILITIES
# ==========================================================

def recreate_database() -> None:
    """
    WARNING:
    Deletes every Storage Engine table and recreates it.

    Intended only for development.
    """

    conn = get_connection()

    conn.execute("PRAGMA foreign_keys = OFF;")

    tables = (
        "storage_containers",
        "storage_positions",
        "storage_boxes",
        "storage_racks",
        "storage_freezers",
    )

    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")

    conn.commit()
    conn.close()

    initialize_database()


if __name__ == "__main__":

    initialize_database()

    print("Storage schema successfully initialized.")