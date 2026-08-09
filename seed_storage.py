"""
seed_storage.py

One-off script to seed a freezer and the lab's real racks, until
the Freezer/Rack management UI exists.

Racks:
    "1".."40"  -> EPPENDORF, no shelves
    "A".."D"   -> FALCON, has shelves (Upper/Lower)

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

    # Numeric racks: 1-40, EPPENDORF, no shelves
    for number in range(1, 41):
        racks.append((str(number), "EPPENDORF"))

    # Lettered racks: A-D, FALCON, with shelves
    # (has_shelf is determined by StorageService.get_rack_configuration,
    # which checks rack_name in ("A", "B", "C", "D") -- no schema
    # change needed here, that logic already exists.)
    for letter in "ABCD":
        racks.append((letter, "FALCON"))

    for rack_name, rack_type in racks:
        conn.execute(
            """
            INSERT INTO storage_racks
            (freezer_id, rack_name, rack_type, description)
            VALUES (?, ?, ?, ?)
            """,
            (freezer_id, rack_name, rack_type, ""),
        )

    conn.commit()
    conn.close()

    print(
        f"Seeded freezer 'Freezer 1' (id={freezer_id}) with "
        f"{len(racks)} racks (1-40 EPPENDORF, A-D FALCON)."
    )


if __name__ == "__main__":
    seed()