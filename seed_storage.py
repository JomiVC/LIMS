"""
seed_storage.py

One-off script to seed a freezer and the lab's real racks, until
the Freezer/Rack management UI exists.

Racks:
    "1".."40"  -> EPPENDORF, no shelves, 5 slots
    "A".."D"   -> FALCON, 2 shelves (Upper/Lower), 3 slots

Run from the project root:
    python seed_storage.py
"""

from database.connection import get_connection


def seed():

    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON;")

    # --- Freezer ---
    cursor = conn.execute(
        """
        INSERT INTO storage_freezers (name, temperature, description)
        VALUES (?, ?, ?)
        """,
        ("Freezer 1", -20.0, "Main -20C freezer"),
    )
    freezer_id = cursor.lastrowid

    racks = []

    # Numeric racks: 1-40, EPPENDORF, no shelves, 5 slots
    for number in range(1, 41):
        racks.append((str(number), "EPPENDORF", 0, 5))

    # Lettered racks: A-D, FALCON, 2 shelves, 3 slots
    for letter in "ABCD":
        racks.append((letter, "FALCON", 1, 3))

    for rack_name, rack_type, has_shelf, slot_count in racks:
        conn.execute(
            """
            INSERT INTO storage_racks
            (freezer_id, rack_name, rack_type, has_shelf,
             slot_count, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (freezer_id, rack_name, rack_type, has_shelf, slot_count, ""),
        )

    conn.commit()
    conn.close()

    print(
        f"Seeded freezer 'Freezer 1' (id={freezer_id}) with "
        f"{len(racks)} racks (1-40 EPPENDORF, A-D FALCON)."
    )


if __name__ == "__main__":
    seed()