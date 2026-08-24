"""
repositories/protein_repository.py

Data access for protein_expressed and protein_purified.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional

from database.connection import get_connection
from database.schema import ensure_protein_consumption_columns, create_protein_usage_history_table
from models.protein import ProteinExpressed, ProteinPurified


class ProteinRepository:

    def ensure_schema(self):
        with self.transaction() as conn:
            ensure_protein_consumption_columns(conn)
            create_protein_usage_history_table(conn)
            # Legacy records predate the remaining-* counters.
            conn.execute(
                """
                UPDATE protein_expressed
                SET remaining_falcons = total_falcons
                WHERE used_falcons = 0 AND remaining_falcons = 0
                """
            )
            conn.execute(
                """
                UPDATE protein_purified
                SET remaining_aliquots = total_aliquots
                WHERE used_aliquots = 0 AND remaining_aliquots = 0
                """
            )
            self._reconcile_storage_containers(conn)

    @contextmanager
    def transaction(self):
        """Public context manager for multi-statement atomic transactions."""
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

    def _conn(self):
        return self.transaction()

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

        with self.transaction() as conn:

            sample_id = self._next_sample_id(
                conn, "protein_expressed", "EXP"
            )

            cursor = conn.execute(
                """
                INSERT INTO protein_expressed
                (
                    sample_id, protein_name, construct, variant,
                    media, batch_no, volume_per_falcon_l, buffer,
                    date_stored, notebook_ref, total_falcons,
                    used_falcons, remaining_falcons, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_id, protein_name, construct, variant,
                    media, batch_no, volume_per_falcon_l, buffer,
                    date_stored, notebook_ref, total_falcons,
                    0, total_falcons, notes,
                )
            )

            return cursor.lastrowid, sample_id

    def get_expressed(self, record_id: int, conn: Optional[sqlite3.Connection] = None) -> ProteinExpressed | None:
        if conn is not None:
            row = conn.execute(
                "SELECT * FROM protein_expressed WHERE id = ?",
                (record_id,)
            ).fetchone()
            return ProteinExpressed.from_row(row) if row else None

        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM protein_expressed WHERE id = ?",
                (record_id,)
            ).fetchone()

        return ProteinExpressed.from_row(row) if row else None

    def list_expressed(self) -> list[ProteinExpressed]:

        with self.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM protein_expressed ORDER BY id DESC"
            ).fetchall()

        return [ProteinExpressed.from_row(r) for r in rows]

    def search_expressed(self, text: str) -> list[ProteinExpressed]:

        with self.transaction() as conn:
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

        with self.transaction() as conn:

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
                    total_aliquots, used_aliquots, remaining_aliquots, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_id, protein_name, construct, variant,
                    media, batch_no, concentration_um, volume_ul,
                    buffer, date_stored, notebook_ref,
                    total_aliquots, 0, total_aliquots, notes,
                )
            )

            return cursor.lastrowid, sample_id

    def create_purified_from_expression(
        self,
        conn: sqlite3.Connection,
        *,
        source_expression_id: int,
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
        """Creates a purified protein record linked to its source expression within an open transaction."""
        sample_id = self._next_sample_id(conn, "protein_purified", "PUR")

        cursor = conn.execute(
            """
            INSERT INTO protein_purified
            (
                sample_id, source_expression_id, protein_name, construct, variant,
                media, batch_no, concentration_um, volume_ul,
                buffer, date_stored, notebook_ref,
                total_aliquots, used_aliquots, remaining_aliquots, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sample_id, source_expression_id, protein_name, construct, variant,
                media, batch_no, concentration_um, volume_ul,
                buffer, date_stored, notebook_ref,
                total_aliquots, 0, total_aliquots, notes,
            )
        )

        return cursor.lastrowid, sample_id

    def get_purified(self, record_id: int) -> ProteinPurified | None:

        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM protein_purified WHERE id = ?",
                (record_id,)
            ).fetchone()

        return ProteinPurified.from_row(row) if row else None

    def list_purified(self) -> list[ProteinPurified]:

        with self.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM protein_purified ORDER BY id DESC"
            ).fetchall()

        return [ProteinPurified.from_row(r) for r in rows]

    def search_purified(self, text: str) -> list[ProteinPurified]:

        with self.transaction() as conn:
            rows = conn.execute(
                """
                SELECT * FROM protein_purified
                WHERE protein_name LIKE ? OR sample_id LIKE ?
                ORDER BY id DESC
                """,
                (f"%{text}%", f"%{text}%")
            ).fetchall()

        return [ProteinPurified.from_row(r) for r in rows]

    def deduct_expression_falcons(
        self,
        conn: sqlite3.Connection,
        expression_id: int,
        falcons_used: int,
        target_purification_sample_id: str,
    ) -> None:
        """Deducts Falcons from an expressed protein and logs the 'Purification' usage event."""
        row = conn.execute(
            "SELECT total_falcons, used_falcons, remaining_falcons FROM protein_expressed WHERE id = ?",
            (expression_id,),
        ).fetchone()

        if row is None:
            raise ValueError(f"Expressed protein record #{expression_id} not found.")

        available = max(int(row["total_falcons"]) - int(row["used_falcons"]), 0)
        if falcons_used < 1:
            raise ValueError("Falcons used must be at least 1.")
        if falcons_used > available:
            raise ValueError(f"Only {available} falcon(s) available in expression #{expression_id}.")

        new_used = int(row["used_falcons"]) + falcons_used
        new_remaining = int(row["total_falcons"]) - new_used

        conn.execute(
            """
            UPDATE protein_expressed
            SET used_falcons = ?, remaining_falcons = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (new_used, new_remaining, expression_id),
        )

        reason_text = f"Purification ({target_purification_sample_id})"
        conn.execute(
            """
            INSERT INTO protein_usage_history (owner_table, owner_id, quantity, reason)
            VALUES (?, ?, ?, ?)
            """,
            ("protein_expressed", expression_id, falcons_used, reason_text),
        )

        self._release_storage_containers(
            conn, "protein_expressed_id", expression_id, falcons_used
        )

    def get_purifications_for_expression(self, expression_id: int) -> list[ProteinPurified]:
        """Finds all purified protein batches derived from a specific expressed protein."""
        with self.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM protein_purified WHERE source_expression_id = ? ORDER BY id DESC",
                (expression_id,),
            ).fetchall()

        return [ProteinPurified.from_row(r) for r in rows]

    def get_source_expression_for_purification(self, purification_id: int) -> ProteinExpressed | None:
        """Finds the source expressed protein for a given purified protein batch."""
        with self.transaction() as conn:
            row = conn.execute(
                """
                SELECT e.* FROM protein_expressed e
                JOIN protein_purified p ON p.source_expression_id = e.id
                WHERE p.id = ?
                """,
                (purification_id,),
            ).fetchone()

        return ProteinExpressed.from_row(row) if row else None

    # =====================================================
    # USAGE TRACKING
    # =====================================================

    @staticmethod
    def _release_storage_containers(
        conn: sqlite3.Connection,
        item_column: str,
        record_id: int,
        quantity: int,
    ) -> None:
        """Free one physical storage position for each consumed aliquot."""
        container_rows = conn.execute(
            f"""
            SELECT c.id
            FROM storage_containers c
            JOIN storage_positions p ON p.id = c.position_id
            WHERE c.{item_column} = ?
            ORDER BY p.box_id, p.position, c.id
            LIMIT ?
            """,
            (record_id, quantity),
        ).fetchall()

        if container_rows:
            conn.executemany(
                "DELETE FROM storage_containers WHERE id = ?",
                [(row["id"],) for row in container_rows],
            )

    @classmethod
    def _reconcile_storage_containers(cls, conn: sqlite3.Connection) -> None:
        """Remove stale containers for aliquots that were consumed earlier."""
        configurations = (
            ("protein_expressed", "protein_expressed_id", "remaining_falcons"),
            ("protein_purified", "protein_purified_id", "remaining_aliquots"),
        )

        for table, item_column, remaining_column in configurations:
            records = conn.execute(
                f"SELECT id, {remaining_column} FROM {table}"
            ).fetchall()
            for record in records:
                container_rows = conn.execute(
                    f"""
                    SELECT c.id
                    FROM storage_containers c
                    JOIN storage_positions p ON p.id = c.position_id
                    WHERE c.{item_column} = ?
                    ORDER BY p.box_id, p.position, c.id
                    """,
                    (record["id"],),
                ).fetchall()
                excess = len(container_rows) - int(record[remaining_column])
                if excess > 0:
                    conn.executemany(
                        "DELETE FROM storage_containers WHERE id = ?",
                        [(row["id"],) for row in container_rows[:excess]],
                    )

    def consume_expressed(self, record_id: int, quantity: int, reason: str | None = None) -> None:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT total_falcons, used_falcons, remaining_falcons FROM protein_expressed WHERE id = ?",
                (record_id,),
            ).fetchone()

            if row is None:
                raise ValueError("Expressed protein record not found.")

            available = max(int(row["total_falcons"]) - int(row["used_falcons"]), 0)
            if quantity < 1:
                raise ValueError("Quantity to use must be at least 1.")
            if quantity > available:
                raise ValueError(f"Only {available} falcon(s) available to use.")

            new_used = int(row["used_falcons"]) + quantity
            new_remaining = int(row["total_falcons"]) - new_used

            conn.execute(
                """
                UPDATE protein_expressed
                SET used_falcons = ?, remaining_falcons = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (new_used, new_remaining, record_id),
            )
            conn.execute(
                """
                INSERT INTO protein_usage_history (owner_table, owner_id, quantity, reason)
                VALUES (?, ?, ?, ?)
                """,
                ("protein_expressed", record_id, quantity, reason or "manual usage"),
            )
            self._release_storage_containers(
                conn, "protein_expressed_id", record_id, quantity
            )

    def consume_purified(self, record_id: int, quantity: int, reason: str | None = None) -> None:
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT total_aliquots, used_aliquots, remaining_aliquots FROM protein_purified WHERE id = ?",
                (record_id,),
            ).fetchone()

            if row is None:
                raise ValueError("Purified protein record not found.")

            available = max(int(row["total_aliquots"]) - int(row["used_aliquots"]), 0)
            if quantity < 1:
                raise ValueError("Quantity to use must be at least 1.")
            if quantity > available:
                raise ValueError(f"Only {available} aliquot(s) available to use.")

            new_used = int(row["used_aliquots"]) + quantity
            new_remaining = int(row["total_aliquots"]) - new_used

            conn.execute(
                """
                UPDATE protein_purified
                SET used_aliquots = ?, remaining_aliquots = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (new_used, new_remaining, record_id),
            )
            conn.execute(
                """
                INSERT INTO protein_usage_history (owner_table, owner_id, quantity, reason)
                VALUES (?, ?, ?, ?)
                """,
                ("protein_purified", record_id, quantity, reason or "manual usage"),
            )
            self._release_storage_containers(
                conn, "protein_purified_id", record_id, quantity
            )

    def list_usage_history(self, owner_table: str, owner_id: int):
        with self.transaction() as conn:
            rows = conn.execute(
                """
                SELECT * FROM protein_usage_history
                WHERE owner_table = ? AND owner_id = ?
                ORDER BY used_at DESC
                """,
                (owner_table, owner_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def search_usage_history(self, text: str = "") -> list[dict]:
        """Return protein usage events, enriched with the protein identity."""
        pattern = f"%{text.strip()}%"

        with self.transaction() as conn:
            rows = conn.execute(
                """
                SELECT
                    h.id,
                    CASE h.owner_table
                        WHEN 'protein_expressed' THEN 'Expressed protein'
                        WHEN 'protein_purified' THEN 'Purified protein'
                    END AS type,
                    COALESCE(e.sample_id, p.sample_id) AS sample_id,
                    COALESCE(e.protein_name, p.protein_name) AS protein_name,
                    h.quantity,
                    h.reason,
                    h.used_at
                FROM protein_usage_history h
                LEFT JOIN protein_expressed e
                    ON h.owner_table = 'protein_expressed' AND h.owner_id = e.id
                LEFT JOIN protein_purified p
                    ON h.owner_table = 'protein_purified' AND h.owner_id = p.id
                WHERE
                    COALESCE(e.sample_id, p.sample_id, '') LIKE ?
                    OR COALESCE(e.protein_name, p.protein_name, '') LIKE ?
                    OR COALESCE(h.reason, '') LIKE ?
                    OR h.owner_table LIKE ?
                ORDER BY h.used_at DESC, h.id DESC
                """,
                (pattern, pattern, pattern, pattern),
            ).fetchall()

        return [dict(row) for row in rows]
