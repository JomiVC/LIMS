"""
repositories/protein_repository.py

Data access for protein_expressed and protein_purified.
"""

import sqlite3
from contextlib import contextmanager

from database.connection import get_connection
from models.protein import ProteinExpressed, ProteinPurified


class ProteinRepository:

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

    def _next_sample_id(
        self, conn: sqlite3.Connection, table: str, prefix: str
    ) -> str:
        """
        Auto-generates a correlative sample id like 'EXP-0001'. Based
        on the highest existing numeric suffix for that prefix, not
        on row count, so it never reuses a number after a deletion.
        """

        row = conn.execute(
            f"""
            SELECT sample_id FROM {table}
            WHERE sample_id LIKE ?
            ORDER BY id DESC LIMIT 1
            """,
            (f"{prefix}-%",)
        ).fetchone()

        if row is None:
            next_n = 1
        else:
            next_n = int(row["sample_id"].split("-")[-1]) + 1

        return f"{prefix}-{next_n:04d}"

    # =====================================================
    # EXPRESSED
    # =====================================================

    def create_expressed(
        self,
        protein_name: str,
        construct: str,
        variant: str,
        media: str,
        batch_no: str,
        volume_per_falcon_l: float | None,
        buffer: str,
        date_stored: str,
        notebook_ref: str,
        total_falcons: int,
        notes: str = "",
    ) -> tuple[int, str]:

        with self._conn() as conn:

            sample_id = self._next_sample_id(
                conn, "protein_expressed", "EXP"
            )

            cursor = conn.execute(
                """
                INSERT INTO protein_expressed
                (
                    sample_id, protein_name, construct, variant,
                    media, batch_no, volume_per_falcon_l, buffer,
                    date_stored, notebook_ref, total_falcons, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_id, protein_name, construct, variant,
                    media, batch_no, volume_per_falcon_l, buffer,
                    date_stored, notebook_ref, total_falcons, notes,
                )
            )

            return cursor.lastrowid, sample_id

    def get_expressed(self, record_id: int) -> ProteinExpressed | None:

        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM protein_expressed WHERE id = ?",
                (record_id,)
            ).fetchone()

        return ProteinExpressed.from_row(row) if row else None

    def list_expressed(self) -> list[ProteinExpressed]:

        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM protein_expressed ORDER BY id DESC"
            ).fetchall()

        return [ProteinExpressed.from_row(r) for r in rows]

    def search_expressed(self, text: str) -> list[ProteinExpressed]:

        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM protein_expressed
                WHERE protein_name LIKE ? OR sample_id LIKE ?
                ORDER BY id DESC
                """,
                (f"%{text}%", f"%{text}%")
            ).fetchall()

        return [ProteinExpressed.from_row(r) for r in rows]

    # =====================================================
    # PURIFIED
    # =====================================================

    def create_purified(
        self,
        protein_name: str,
        construct: str,
        variant: str,
        media: str,
        batch_no: str,
        concentration_um: float | None,
        volume_ul: float | None,
        buffer: str,
        date_stored: str,
        notebook_ref: str,
        total_aliquots: int,
        notes: str = "",
    ) -> tuple[int, str]:

        with self._conn() as conn:

            sample_id = self._next_sample_id(
                conn, "protein_purified", "PUR"
            )

            cursor = conn.execute(
                """
                INSERT INTO protein_purified
                (
                    sample_id, protein_name, construct, variant,
                    media, batch_no, concentration_um, volume_ul,
                    buffer, date_stored, notebook_ref,
                    total_aliquots, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_id, protein_name, construct, variant,
                    media, batch_no, concentration_um, volume_ul,
                    buffer, date_stored, notebook_ref,
                    total_aliquots, notes,
                )
            )

            return cursor.lastrowid, sample_id

    def get_purified(self, record_id: int) -> ProteinPurified | None:

        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM protein_purified WHERE id = ?",
                (record_id,)
            ).fetchone()

        return ProteinPurified.from_row(row) if row else None

    def list_purified(self) -> list[ProteinPurified]:

        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM protein_purified ORDER BY id DESC"
            ).fetchall()

        return [ProteinPurified.from_row(r) for r in rows]

    def search_purified(self, text: str) -> list[ProteinPurified]:

        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM protein_purified
                WHERE protein_name LIKE ? OR sample_id LIKE ?
                ORDER BY id DESC
                """,
                (f"%{text}%", f"%{text}%")
            ).fetchall()

        return [ProteinPurified.from_row(r) for r in rows]