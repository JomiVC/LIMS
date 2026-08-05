"""
database/seed.py

Initial data for the LIMS database.

Creates the physical structure of the laboratory.

Version: 1.0
"""

from sqlite3 import Connection

from database.connection import get_connection


# ==========================================================
# LAB CONFIGURATION
# ==========================================================

FREEZER_NAME = "Freezer -80"

FREEZER_TEMPERATURE = -80.0


EPPENDORF_RACKS = list(range(1, 41))

FALCON_RACKS = ["A", "B", "C", "D"]


# ==========================================================
# PUBLIC API
# ==========================================================

def initialize_storage() -> None:

    conn = get_connection()

    conn.execute("PRAGMA foreign_keys = ON;")

    freezer_id = create_freezer(conn)

    create_eppendorf_racks(conn, freezer_id)

    create_falcon_racks(conn, freezer_id)

    conn.commit()

    conn.close()


# ==========================================================
# FREEZER
# ==========================================================

def create_freezer(conn: Connection) -> int:

    cursor = conn.execute(
        """
        SELECT id
        FROM storage_freezers
        WHERE name = ?
        """,
        (FREEZER_NAME,)
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    cursor = conn.execute(
        """
        INSERT INTO storage_freezers
        (
            name,
            temperature,
            description
        )
        VALUES (?, ?, ?)
        """,
        (
            FREEZER_NAME,
            FREEZER_TEMPERATURE,
            "Main laboratory freezer"
        )
    )

    return cursor.lastrowid


# ==========================================================
# RACKS
# ==========================================================

def create_eppendorf_racks(
    conn: Connection,
    freezer_id: int
) -> None:

    for rack in EPPENDORF_RACKS:

        conn.execute(
            """
            INSERT OR IGNORE INTO storage_racks
            (
                freezer_id,
                rack_name,
                rack_type,
                description
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                freezer_id,
                str(rack),
                "EPPENDORF",
                f"Eppendorf rack {rack}"
            )
        )


def create_falcon_racks(
    conn: Connection,
    freezer_id: int
) -> None:

    for rack in FALCON_RACKS:

        conn.execute(
            """
            INSERT OR IGNORE INTO storage_racks
            (
                freezer_id,
                rack_name,
                rack_type,
                description
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                freezer_id,
                rack,
                "FALCON",
                f"Falcon rack {rack}"
            )
        )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    initialize_storage()

    print("Storage successfully initialized.")