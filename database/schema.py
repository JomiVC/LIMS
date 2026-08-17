"""
database/schema.py

LIMS Database Schema

Storage Engine v1.1
- storage_containers now links to a real item (DNA, protein
  aliquot, or reagent lot) via exclusive FKs instead of a free
  container_type string.
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

    create_dna_stock_table(conn)
    create_protein_expressed_table(conn)
    create_protein_purified_table(conn)
    create_reagent_lots_table(conn)
    create_attachments_table(conn)

    create_storage_containers_table(conn)

    create_indexes(conn)
    create_item_link_indexes(conn)
    create_protein_indexes(conn)

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

            has_shelf INTEGER NOT NULL DEFAULT 0
                CHECK(has_shelf IN (0,1)),

            slot_count INTEGER NOT NULL DEFAULT 5
                CHECK(slot_count > 0),

            description TEXT,

            FOREIGN KEY(freezer_id)
                REFERENCES storage_freezers(id)
                ON DELETE RESTRICT,

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
                CHECK(box_type IN ('EPPENDORF','FALCON','FALCON_15')),
            -- 'FALCON' = Falcon 50ml (4x4 grid)
            -- 'FALCON_15' = Falcon 15ml (7x7 grid)

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


# ==========================================================
# ITEM STUB TABLES
# (flesh out with real columns when each module is built)
# ==========================================================

def create_dna_stock_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dna_stock (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            notes TEXT

        );
        """
    )


def create_protein_expressed_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS protein_expressed (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sample_id TEXT NOT NULL UNIQUE,
            -- auto-generated (e.g. "EXP-0001"), never entered
            -- by hand -- see services/protein_service.py

            protein_name TEXT NOT NULL,
            construct TEXT,
            variant TEXT,
            media TEXT,

            batch_no TEXT,

            volume_per_falcon_l REAL,
            -- litres, as specified (not a typo)

            buffer TEXT,

            date_stored TEXT,
            notebook_ref TEXT,

            total_falcons INTEGER NOT NULL,
            -- how many Falcons this batch was split into --
            -- matches the number of storage_containers rows
            -- created for this record

            notes TEXT,

            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))

        );
        """
    )


def create_protein_purified_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS protein_purified (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sample_id TEXT NOT NULL UNIQUE,
            -- auto-generated (e.g. "PUR-0001")

            protein_name TEXT NOT NULL,
            construct TEXT,
            variant TEXT,
            media TEXT,

            batch_no TEXT,

            concentration_um REAL,
            volume_ul REAL,

            buffer TEXT,

            date_stored TEXT,
            notebook_ref TEXT,

            total_aliquots INTEGER NOT NULL,
            -- matches the number of storage_containers rows
            -- created for this record

            notes TEXT,

            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))

        );
        """
    )


def create_attachments_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attachments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Which record this file belongs to. Polymorphic by
            -- design (unlike storage_containers' exclusive FKs)
            -- because the set of attachable tables will keep
            -- growing as new modules are built, and adding a
            -- column to this table per module would be worse
            -- than the loss of DB-level referential integrity
            -- here. The owning module is responsible for not
            -- leaving orphaned rows (e.g. delete attachments when
            -- deleting the parent record).
            owner_table TEXT NOT NULL,
            owner_id INTEGER NOT NULL,

            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            -- relative path under storage/attachments/, per config.py

            uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))

        );
        """
    )

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_attachments_owner
        ON attachments(owner_table, owner_id);
    """)



def create_reagent_lots_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reagent_lots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            notes TEXT

        );
        """
    )


# ==========================================================
# CONTAINERS
# ==========================================================

def create_storage_containers_table(conn: Connection) -> None:

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS storage_containers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            container_type TEXT NOT NULL
                CHECK(
                    container_type IN (
                        'DNA',
                        'PROTEIN_EXPRESSED',
                        'PROTEIN_PURIFIED',
                        'REAGENT_LOT'
                    )
                ),

            position_id INTEGER NOT NULL UNIQUE,

            dna_id INTEGER,
            protein_expressed_id INTEGER,
            protein_purified_id INTEGER,
            reagent_lot_id INTEGER,

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

            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),

            notes TEXT,

            FOREIGN KEY(position_id)
                REFERENCES storage_positions(id)
                ON DELETE RESTRICT,

            FOREIGN KEY(dna_id)
                REFERENCES dna_stock(id)
                ON DELETE RESTRICT,

            FOREIGN KEY(protein_expressed_id)
                REFERENCES protein_expressed(id)
                ON DELETE RESTRICT,

            FOREIGN KEY(protein_purified_id)
                REFERENCES protein_purified(id)
                ON DELETE RESTRICT,

            FOREIGN KEY(reagent_lot_id)
                REFERENCES reagent_lots(id)
                ON DELETE RESTRICT,

            CHECK(
                (
                    (dna_id IS NOT NULL) +
                    (protein_expressed_id IS NOT NULL) +
                    (protein_purified_id IS NOT NULL) +
                    (reagent_lot_id IS NOT NULL)
                ) = 1
            ),

            CHECK(
                (container_type = 'DNA'
                    AND dna_id IS NOT NULL) OR
                (container_type = 'PROTEIN_EXPRESSED'
                    AND protein_expressed_id IS NOT NULL) OR
                (container_type = 'PROTEIN_PURIFIED'
                    AND protein_purified_id IS NOT NULL) OR
                (container_type = 'REAGENT_LOT'
                    AND reagent_lot_id IS NOT NULL)
            )

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
        CREATE INDEX IF NOT EXISTS idx_boxes_owner
        ON storage_boxes(owner);
    """)


def create_item_link_indexes(conn: Connection) -> None:

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_containers_position
        ON storage_containers(position_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_containers_dna
        ON storage_containers(dna_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_containers_reagent
        ON storage_containers(reagent_lot_id);
    """)


def create_protein_indexes(conn: Connection) -> None:

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_containers_protein_expressed
        ON storage_containers(protein_expressed_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_containers_protein_purified
        ON storage_containers(protein_purified_id);
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
        "dna_stock",
        "protein_expressed",
        "protein_purified",
        "reagent_lots",
        "attachments",
    )

    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")

    conn.commit()
    conn.close()

    initialize_database()


if __name__ == "__main__":

    initialize_database()

    print("Storage schema successfully initialized.")