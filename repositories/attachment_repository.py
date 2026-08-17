"""
repositories/attachment_repository.py

Data access for the generic `attachments` table.
"""

import sqlite3
from contextlib import contextmanager

from database.connection import get_connection


class AttachmentRepository:

    @contextmanager
    def _conn(self):

        conn = get_connection()

        try:
            yield conn
            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    def create(
        self,
        owner_table: str,
        owner_id: int,
        file_name: str,
        file_path: str,
    ) -> int:

        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO attachments
                (owner_table, owner_id, file_name, file_path)
                VALUES (?, ?, ?, ?)
                """,
                (owner_table, owner_id, file_name, file_path)
            )
            return cursor.lastrowid

    def list_for(
        self, owner_table: str, owner_id: int
    ) -> list[sqlite3.Row]:

        with self._conn() as conn:
            return conn.execute(
                """
                SELECT * FROM attachments
                WHERE owner_table = ? AND owner_id = ?
                ORDER BY uploaded_at
                """,
                (owner_table, owner_id)
            ).fetchall()

    def delete(self, attachment_id: int) -> None:

        with self._conn() as conn:
            conn.execute(
                "DELETE FROM attachments WHERE id = ?",
                (attachment_id,)
            )