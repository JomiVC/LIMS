"""
repositories/storage_repository.py

Storage Repository

All database operations related to laboratory storage.

Changes vs previous version:
- Returns domain models (models.storage.*) instead of raw sqlite3.Row.
- Opens a fresh connection per operation instead of holding one open
  for the lifetime of the repository instance (safer with Streamlit's
  rerun model and avoids leaking open SQLite connections).
- create_box / move_box validate that the target rack exists.
- create_positions raises a clear error instead of failing on the
  UNIQUE constraint if positions already exist for the box.
- delete_box checks for occupied positions first and raises a
  domain-level error instead of relying on the FK RESTRICT to fail.
"""

import sqlite3
from contextlib import contextmanager

from database.connection import get_connection
from models.storage import Freezer, Rack, Box, Position, Container


# ==========================================================
# DOMAIN ERRORS
# ==========================================================

class StorageError(Exception):
    """Base class for storage-related business rule violations."""


class RackNotFoundError(StorageError):
    pass


class BoxNotEmptyError(StorageError):
    pass


class PositionsAlreadyExistError(StorageError):
    pass


class DuplicateBoxNameError(StorageError):
    pass


class RackAlreadyExistsError(StorageError):
    pass


class FreezerAlreadyExistsError(StorageError):
    pass


class SlotOccupiedError(StorageError):
    pass


class DuplicatePositionError(StorageError):
    pass


class StorageRepository:

    # =====================================================
    # CONNECTION HANDLING
    # =====================================================

    @contextmanager
    def _conn(self):
        """
        Yields a connection scoped to a single operation.

        Commits on success, rolls back on exception, always closes.
        """

        conn = get_connection()
        conn.execute("PRAGMA foreign_keys = ON;")

        try:
            yield conn
            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    # =====================================================
    # FREEZERS
    # =====================================================

    def list_freezers(self) -> list[Freezer]:

        with self._conn() as conn:

            cursor = conn.execute(
                "SELECT * FROM storage_freezers ORDER BY name"
            )

            return [Freezer.from_row(row) for row in cursor.fetchall()]

    def get_freezer(self, freezer_id: int) -> Freezer | None:

        with self._conn() as conn:

            row = conn.execute(
                "SELECT * FROM storage_freezers WHERE id = ?",
                (freezer_id,)
            ).fetchone()

        return Freezer.from_row(row) if row else None

    def create_freezer(
        self,
        name: str,
        temperature: float | None,
        description: str = ""
    ) -> int:

        with self._conn() as conn:

            existing = conn.execute(
                "SELECT 1 FROM storage_freezers WHERE name = ?",
                (name,)
            ).fetchone()

            if existing:
                raise FreezerAlreadyExistsError(
                    f"A freezer named '{name}' already exists."
                )

            cursor = conn.execute(
                """
                INSERT INTO storage_freezers
                (name, temperature, description)
                VALUES (?, ?, ?)
                """,
                (name, temperature, description)
            )

            return cursor.lastrowid

    # =====================================================
    # RACKS
    # =====================================================

    def list_racks(self) -> list[Rack]:

        with self._conn() as conn:

            cursor = conn.execute(
                """
                SELECT *
                FROM storage_racks
                """
            )

            racks = [Rack.from_row(row) for row in cursor.fetchall()]

        numeric = [r for r in racks if r.rack_name.isdigit()]
        alpha = [r for r in racks if not r.rack_name.isdigit()]

        numeric.sort(key=lambda r: int(r.rack_name))
        alpha.sort(key=lambda r: r.rack_name)

        return numeric + alpha

    def get_rack(self, rack_id: int) -> Rack | None:

        with self._conn() as conn:

            cursor = conn.execute(
                """
                SELECT *
                FROM storage_racks
                WHERE id = ?
                """,
                (rack_id,)
            )

            row = cursor.fetchone()

        return Rack.from_row(row) if row else None

    def create_rack(
        self,
        freezer_id: int,
        rack_name: str,
        rack_type: str,
        has_shelf: bool,
        slot_count: int,
        description: str = ""
    ) -> int:
        """
        Not yet exposed in any page -- the lab's racks were seeded
        directly for now. Wire this up once a Rack management UI
        exists.
        """

        with self._conn() as conn:

            existing = conn.execute(
                """
                SELECT 1 FROM storage_racks
                WHERE freezer_id = ? AND rack_name = ?
                """,
                (freezer_id, rack_name)
            ).fetchone()

            if existing:
                raise RackAlreadyExistsError(
                    f"Rack '{rack_name}' already exists in this freezer."
                )

            cursor = conn.execute(
                """
                INSERT INTO storage_racks
                (freezer_id, rack_name, rack_type, has_shelf,
                 slot_count, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    freezer_id,
                    rack_name,
                    rack_type,
                    int(has_shelf),
                    slot_count,
                    description,
                )
            )

            return cursor.lastrowid

    def _rack_exists(self, conn: sqlite3.Connection, rack_id: int) -> bool:

        cursor = conn.execute(
            "SELECT 1 FROM storage_racks WHERE id = ?",
            (rack_id,)
        )

        return cursor.fetchone() is not None

    def _slot_occupied(
        self,
        conn: sqlite3.Connection,
        rack_id: int,
        shelf,
        slot: int,
        exclude_box_id: int | None = None
    ) -> bool:
        """
        `shelf` may be None (racks without shelves) -- 'IS ?' is
        used instead of '=' so the NULL comparison works correctly.
        """

        query = (
            "SELECT id FROM storage_boxes "
            "WHERE rack_id = ? AND slot = ? AND shelf IS ?"
        )
        params = [rack_id, slot, shelf]

        if exclude_box_id is not None:
            query += " AND id != ?"
            params.append(exclude_box_id)

        return conn.execute(query, params).fetchone() is not None

    # =====================================================
    # BOXES
    # =====================================================

    def create_box(
        self,
        box_name: str,
        box_type: str,
        owner: str,
        rack_id: int,
        shelf: int,
        slot: int,
        notes: str = ""
    ) -> int:

        with self._conn() as conn:

            if not self._rack_exists(conn, rack_id):
                raise RackNotFoundError(
                    f"Rack {rack_id} does not exist."
                )

            existing = conn.execute(
                "SELECT 1 FROM storage_boxes WHERE box_name = ?",
                (box_name,)
            ).fetchone()

            if existing:
                raise DuplicateBoxNameError(
                    f"A box named '{box_name}' already exists."
                )

            if self._slot_occupied(conn, rack_id, shelf, slot):
                raise SlotOccupiedError(
                    f"Slot {slot}"
                    f"{f' ({shelf})' if shelf else ''} in this rack "
                    f"is already occupied by another box."
                )

            cursor = conn.execute(
                """
                INSERT INTO storage_boxes
                (
                    box_name,
                    box_type,
                    owner,
                    rack_id,
                    shelf,
                    slot,
                    notes
                )
                VALUES
                (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    box_name,
                    box_type,
                    owner,
                    rack_id,
                    shelf,
                    slot,
                    notes
                )
            )

            return cursor.lastrowid

    def update_box(
        self,
        box_id: int,
        rack_id: int,
        shelf: int,
        slot: int,
        owner: str,
        notes: str
    ) -> None:
        """
        Updates location (rack/shelf/slot), owner, and notes.

        Deliberately does NOT allow changing box_name (unique
        identifier) or box_type (positions were already created
        based on it -- changing it would desync the position grid
        from the box's declared type).
        """

        with self._conn() as conn:

            if not self._rack_exists(conn, rack_id):
                raise RackNotFoundError(
                    f"Rack {rack_id} does not exist."
                )

            if self._slot_occupied(
                conn, rack_id, shelf, slot, exclude_box_id=box_id
            ):
                raise SlotOccupiedError(
                    f"Slot {slot}"
                    f"{f' ({shelf})' if shelf else ''} in this rack "
                    f"is already occupied by another box."
                )

            conn.execute(
                """
                UPDATE storage_boxes
                SET
                    rack_id = ?,
                    shelf = ?,
                    slot = ?,
                    owner = ?,
                    notes = ?
                WHERE id = ?
                """,
                (
                    rack_id,
                    shelf,
                    slot,
                    owner,
                    notes,
                    box_id
                )
            )

    def delete_box(self, box_id: int) -> None:

        with self._conn() as conn:

            occupied = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM storage_positions p
                JOIN storage_containers c
                    ON c.position_id = p.id
                WHERE p.box_id = ?
                """,
                (box_id,)
            ).fetchone()["n"]

            if occupied > 0:
                raise BoxNotEmptyError(
                    f"Box {box_id} still has {occupied} occupied "
                    f"position(s). Remove or relocate containers "
                    f"before deleting the box."
                )

            conn.execute(
                "DELETE FROM storage_boxes WHERE id = ?",
                (box_id,)
            )

    def get_box(self, box_id: int) -> Box | None:

        with self._conn() as conn:

            row = conn.execute(
                "SELECT * FROM storage_boxes WHERE id = ?",
                (box_id,)
            ).fetchone()

        return Box.from_row(row) if row else None

    def get_box_by_name(self, box_name: str) -> Box | None:

        with self._conn() as conn:

            row = conn.execute(
                "SELECT * FROM storage_boxes WHERE box_name = ?",
                (box_name,)
            ).fetchone()

        return Box.from_row(row) if row else None

    def list_boxes(self) -> list[Box]:

        with self._conn() as conn:

            cursor = conn.execute(
                """
                SELECT b.*
                FROM storage_boxes b
                JOIN storage_racks r
                    ON b.rack_id = r.id
                """
            )

            return [Box.from_row(row) for row in cursor.fetchall()]

    def move_box(
        self,
        box_id: int,
        rack_id: int,
        shelf: int,
        slot: int
    ) -> None:

        with self._conn() as conn:

            if not self._rack_exists(conn, rack_id):
                raise RackNotFoundError(
                    f"Rack {rack_id} does not exist."
                )

            conn.execute(
                """
                UPDATE storage_boxes
                SET
                    rack_id = ?,
                    shelf = ?,
                    slot = ?
                WHERE id = ?
                """,
                (
                    rack_id,
                    shelf,
                    slot,
                    box_id
                )
            )

    # =====================================================
    # POSITIONS
    # =====================================================

    def create_positions(
        self,
        box_id: int,
        box_type: str
    ) -> None:

        with self._conn() as conn:

            existing = conn.execute(
                "SELECT 1 FROM storage_positions WHERE box_id = ?",
                (box_id,)
            ).fetchone()

            if existing:
                raise PositionsAlreadyExistError(
                    f"Box {box_id} already has positions created."
                )

            if box_type.upper() == "EPPENDORF":
                rows, cols = "ABCDEFGH", range(1, 9)

            elif box_type.upper() == "FALCON":
                rows, cols = "ABCD", range(1, 5)

            elif box_type.upper() == "FALCON_15":
                rows, cols = "ABCDEFG", range(1, 8)

            else:
                raise ValueError(f"Unknown box type: {box_type}")

            positions = [
                (box_id, f"{row}{col}")
                for row in rows
                for col in cols
            ]

            conn.executemany(
                """
                INSERT INTO storage_positions (box_id, position)
                VALUES (?, ?)
                """,
                positions
            )

    def list_positions(self, box_id: int) -> list[Position]:

        with self._conn() as conn:

            cursor = conn.execute(
                """
                SELECT *
                FROM storage_positions
                WHERE box_id = ?
                ORDER BY position
                """,
                (box_id,)
            )

            return [Position.from_row(row) for row in cursor.fetchall()]

    def get_position(self, position_id: int) -> Position | None:

        with self._conn() as conn:

            row = conn.execute(
                "SELECT * FROM storage_positions WHERE id = ?",
                (position_id,)
            ).fetchone()

        return Position.from_row(row) if row else None

    def get_position_by_name(
        self,
        box_id: int,
        position: str
    ) -> Position | None:

        with self._conn() as conn:

            row = conn.execute(
                """
                SELECT *
                FROM storage_positions
                WHERE box_id = ? AND position = ?
                """,
                (box_id, position)
            ).fetchone()

        return Position.from_row(row) if row else None

    def list_free_positions(self, box_id: int) -> list[Position]:

        with self._conn() as conn:

            cursor = conn.execute(
                """
                SELECT p.*
                FROM storage_positions p
                LEFT JOIN storage_containers c
                    ON p.id = c.position_id
                WHERE p.box_id = ? AND c.id IS NULL
                ORDER BY p.position
                """,
                (box_id,)
            )

            return [Position.from_row(row) for row in cursor.fetchall()]

    def list_occupied_positions(self, box_id: int) -> list[dict]:
        """
        Returns raw dicts (position + container) rather than a single
        model, since this is a join across two entities. Callers that
        need model instances should fetch Position/Container
        separately by id.
        """

        with self._conn() as conn:

            cursor = conn.execute(
                """
                SELECT
                    p.id AS position_id,
                    p.position,
                    c.id AS container_id,
                    c.label,
                    c.container_type
                FROM storage_positions p
                JOIN storage_containers c
                    ON p.id = c.position_id
                WHERE p.box_id = ?
                ORDER BY p.position
                """,
                (box_id,)
            )

            return [dict(row) for row in cursor.fetchall()]

    # =====================================================
    # CONTAINERS
    # =====================================================

    # Maps container_type -> which FK column on storage_containers
    # holds the link, and which table that FK must point to.
    _ITEM_LINK_COLUMNS = {
        "DNA": ("dna_id", "dna_stock"),
        "PROTEIN_EXPRESSED": (
            "protein_expressed_id", "protein_expressed"
        ),
        "PROTEIN_PURIFIED": (
            "protein_purified_id", "protein_purified"
        ),
        "REAGENT_LOT": ("reagent_lot_id", "reagent_lots"),
    }

    def create_container(
        self,
        position_id: int,
        container_type: str,
        item_id: int,
        label: str,
        notes: str = ""
    ) -> int:
        """
        Creates a container at `position_id` holding the item
        identified by `item_id`, whose type is `container_type`
        (one of models.storage.CONTAINER_TYPES).

        `item_id` must already exist in the matching item table
        (dna_stock / protein_expressed / protein_purified /
        reagent_lots) -- this is
        enforced by the FK, but we check explicitly first to raise
        a clear domain error instead of a raw IntegrityError.
        """

        if container_type not in self._ITEM_LINK_COLUMNS:
            raise ValueError(
                f"Unknown container_type: {container_type}"
            )

        column, item_table = self._ITEM_LINK_COLUMNS[container_type]

        with self._conn() as conn:

            occupied = conn.execute(
                "SELECT 1 FROM storage_containers WHERE position_id = ?",
                (position_id,)
            ).fetchone()

            if occupied:
                raise DuplicatePositionError(
                    f"Position {position_id} is already occupied."
                )

            item_exists = conn.execute(
                f"SELECT 1 FROM {item_table} WHERE id = ?",
                (item_id,)
            ).fetchone()

            if not item_exists:
                raise StorageError(
                    f"{container_type} item {item_id} does not "
                    f"exist in {item_table}."
                )

            cursor = conn.execute(
                f"""
                INSERT INTO storage_containers
                (
                    position_id,
                    container_type,
                    {column},
                    label,
                    notes,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    ?, ?, ?, ?, ?,
                    datetime('now'),
                    datetime('now')
                )
                """,
                (
                    position_id,
                    container_type,
                    item_id,
                    label,
                    notes
                )
            )

            return cursor.lastrowid

    def get_container(self, container_id: int) -> Container | None:

        with self._conn() as conn:

            row = conn.execute(
                "SELECT * FROM storage_containers WHERE id = ?",
                (container_id,)
            ).fetchone()

        return Container.from_row(row) if row else None

    def get_container_by_label(self, label: str) -> Container | None:

        with self._conn() as conn:

            row = conn.execute(
                "SELECT * FROM storage_containers WHERE label = ?",
                (label,)
            ).fetchone()

        return Container.from_row(row) if row else None

    def delete_container(self, container_id: int) -> None:

        with self._conn() as conn:

            conn.execute(
                "DELETE FROM storage_containers WHERE id = ?",
                (container_id,)
            )

    def get_container_for_item(self, container_type: str, item_id: int):
        """
        Finds the container (and its full location path) currently
        holding a given item, if any. Used by the Samples search.
        """

        column, _ = self._ITEM_LINK_COLUMNS[container_type]

        with self._conn() as conn:

            row = conn.execute(
                f"""
                SELECT
                    c.id,
                    c.label,
                    p.position,
                    b.box_name,
                    r.rack_name
                FROM storage_containers c
                JOIN storage_positions p ON c.position_id = p.id
                JOIN storage_boxes b ON p.box_id = b.id
                JOIN storage_racks r ON b.rack_id = r.id
                WHERE c.{column} = ?
                """,
                (item_id,)
            ).fetchone()

        return dict(row) if row else None

    def search_containers(self, text: str) -> list[dict]:
        """
        Returns raw dicts since this is a denormalized join across
        the full hierarchy (container + position + box + rack),
        used for display/search rather than as a domain entity.
        """

        with self._conn() as conn:

            cursor = conn.execute(
                """
                SELECT
                    c.id,
                    c.label,
                    c.container_type,
                    p.position,
                    b.box_name,
                    r.rack_name
                FROM storage_containers c
                JOIN storage_positions p ON c.position_id = p.id
                JOIN storage_boxes b ON p.box_id = b.id
                JOIN storage_racks r ON b.rack_id = r.id
                WHERE c.label LIKE ?
                ORDER BY c.label
                """,
                (f"%{text}%",)
            )

            return [dict(row) for row in cursor.fetchall()]