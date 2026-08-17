"""
repositories/item_repository.py

Minimal repository for the remaining item stub tables (dna_stock,
reagent_lots). Proteins are no longer here -- they have real tables
now (protein_expressed, protein_purified) with their own dedicated
repository as part of the Proteins module.

These tables are intentionally minimal (id, name, notes) until the
real DNA / Reagent modules are built.
"""

import sqlite3
from contextlib import contextmanager

from database.connection import get_connection


class ItemNotFoundError(Exception):
    pass


class ItemRepository:

    @contextmanager
    def _conn(self):

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
    # DNA STOCK
    # =====================================================

    def list_dna(self) -> list[sqlite3.Row]:

        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM dna_stock ORDER BY name"
            ).fetchall()

    def get_dna(self, dna_id: int) -> sqlite3.Row | None:

        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM dna_stock WHERE id = ?", (dna_id,)
            ).fetchone()

    def create_dna(self, name: str, notes: str = "") -> int:

        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO dna_stock (name, notes) VALUES (?, ?)",
                (name, notes)
            )
            return cursor.lastrowid

    # =====================================================
    # REAGENT LOTS
    # =====================================================

    def list_reagents(self) -> list[sqlite3.Row]:

        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM reagent_lots ORDER BY name"
            ).fetchall()

    def get_reagent(self, reagent_id: int) -> sqlite3.Row | None:

        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM reagent_lots WHERE id = ?",
                (reagent_id,)
            ).fetchone()

    def create_reagent(self, name: str, notes: str = "") -> int:

        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO reagent_lots (name, notes) VALUES (?, ?)",
                (name, notes)
            )
            return cursor.lastrowid

    # =====================================================
    # GENERIC
    # =====================================================

    _TABLES = {
        "DNA": "dna_stock",
        "REAGENT_LOT": "reagent_lots",
    }

    def get_item_name(self, container_type: str, item_id: int) -> str:

        table = self._TABLES.get(container_type)

        if table is None:
            raise ValueError(f"Unknown container_type: {container_type}")

        with self._conn() as conn:
            row = conn.execute(
                f"SELECT name FROM {table} WHERE id = ?", (item_id,)
            ).fetchone()

        if row is None:
            raise ItemNotFoundError(
                f"{container_type} item {item_id} not found."
            )

        return row["name"]