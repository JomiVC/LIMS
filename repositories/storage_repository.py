"""
repositories/storage_repository.py

Storage Repository

All SQL queries related to the Storage Engine.
"""

import sqlite3

from database.connection import get_connection


class StorageRepository:

    def __init__(self):

        self.conn = get_connection()

        self.conn.row_factory = sqlite3.Row


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

        cursor = self.conn.execute(
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

        self.conn.commit()

        return cursor.lastrowid


    def get_box(self, box_id: int):

        cursor = self.conn.execute(
            """
            SELECT *
            FROM storage_boxes
            WHERE id = ?
            """,
            (box_id,)
        )

        return cursor.fetchone()


    def get_box_by_name(self, name: str):

        cursor = self.conn.execute(
            """
            SELECT *
            FROM storage_boxes
            WHERE box_name = ?
            """,
            (name,)
        )

        return cursor.fetchone()


    def list_boxes(self):

        cursor = self.conn.execute(
            """
            SELECT
                b.*,
                r.rack_name
            FROM storage_boxes b
            JOIN storage_racks r
                ON b.rack_id = r.id
            ORDER BY
                r.rack_name,
                b.slot
            """
        )

        return cursor.fetchall()


    def delete_box(self, box_id: int):

        self.conn.execute(
            """
            DELETE
            FROM storage_boxes
            WHERE id = ?
            """,
            (box_id,)
        )

        self.conn.commit()


    def move_box(
        self,
        box_id: int,
        rack_id: int,
        shelf: int,
        slot: int
    ):

        self.conn.execute(
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

        self.conn.commit()
        # =====================================================
    # POSITIONS
    # =====================================================

    def create_positions(self, box_id: int, box_type: str):

        positions = []

        if box_type.upper() == "EPPENDORF":

            rows = "ABCDEFGH"

            cols = range(1, 9)

        elif box_type.upper() == "FALCON":

            rows = "ABCD"

            cols = range(1, 5)

        else:

            raise ValueError(f"Unknown box type: {box_type}")

        for row in rows:

            for col in cols:

                position = f"{row}{col}"

                positions.append(
                    (
                        box_id,
                        position
                    )
                )

        self.conn.executemany(
            """
            INSERT INTO storage_positions
            (
                box_id,
                position
            )
            VALUES
            (?, ?)
            """,
            positions
        )

        self.conn.commit()


    def list_positions(self, box_id: int):

        cursor = self.conn.execute(
            """
            SELECT *
            FROM storage_positions
            WHERE box_id = ?
            ORDER BY position
            """,
            (box_id,)
        )

        return cursor.fetchall()


    def get_position(self, position_id: int):

        cursor = self.conn.execute(
            """
            SELECT *
            FROM storage_positions
            WHERE id = ?
            """,
            (position_id,)
        )

        return cursor.fetchone()


    # =====================================================
    # CONTAINERS
    # =====================================================

    def assign_container(
        self,
        position_id: int,
        container_type: str,
        label: str,
        notes: str = ""
    ) -> int:

        cursor = self.conn.execute(
            """
            INSERT INTO storage_containers
            (
                container_type,
                position_id,
                label,
                notes,
                created_at,
                updated_at
            )
            VALUES
            (
                ?, ?, ?, ?,
                datetime('now'),
                datetime('now')
            )
            """,
            (
                container_type,
                position_id,
                label,
                notes
            )
        )

        self.conn.commit()

        return cursor.lastrowid


    def remove_container(self, container_id: int):

        self.conn.execute(
            """
            DELETE
            FROM storage_containers
            WHERE id = ?
            """,
            (container_id,)
        )

        self.conn.commit()


    def search_container(self, label: str):

        cursor = self.conn.execute(
            """
            SELECT
                c.id,
                c.label,
                c.container_type,
                p.position,
                b.box_name,
                r.rack_name
            FROM storage_containers c

            JOIN storage_positions p
                ON c.position_id = p.id

            JOIN storage_boxes b
                ON p.box_id = b.id

            JOIN storage_racks r
                ON b.rack_id = r.id

            WHERE c.label LIKE ?

            ORDER BY c.label
            """,
            (f"%{label}%",)
        )

        return cursor.fetchall()


    # =====================================================
    # CLEANUP
    # =====================================================

    def close(self):

        self.conn.close()