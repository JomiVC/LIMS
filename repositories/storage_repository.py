"""
repositories/storage_repository.py

Storage Repository

All database operations related to laboratory storage.
"""

import sqlite3

from database.connection import get_connection


class StorageRepository:

    def __init__(self):

        self.conn = get_connection()
        self.conn.row_factory = sqlite3.Row

    # =====================================================
    # RACKS
    # =====================================================

    def list_racks(self):

        cursor = self.conn.execute(
            """
            SELECT
                id,
                rack_name,
                rack_type
            FROM storage_racks
            """
        )

        racks = cursor.fetchall()

        numeric = []
        alpha = []

        for rack in racks:

            if rack["rack_name"].isdigit():

                numeric.append(rack)

            else:

                alpha.append(rack)

        numeric.sort(key=lambda r: int(r["rack_name"]))
        alpha.sort(key=lambda r: r["rack_name"])

        return numeric + alpha


    def get_rack(self, rack_id):

        cursor = self.conn.execute(
            """
            SELECT *
            FROM storage_racks
            WHERE id = ?
            """,
            (rack_id,)
        )

        return cursor.fetchone()


    # =====================================================
    # BOXES
    # =====================================================

    def create_box(
        self,
        box_name,
        box_type,
        owner,
        rack_id,
        shelf,
        slot,
        notes=""
    ):

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


    def update_box(
        self,
        box_id,
        rack_id,
        shelf,
        slot,
        notes
    ):

        self.conn.execute(
            """
            UPDATE storage_boxes
            SET
                rack_id = ?,
                shelf = ?,
                slot = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                rack_id,
                shelf,
                slot,
                notes,
                box_id
            )
        )

        self.conn.commit()


    def delete_box(self, box_id):

        self.conn.execute(
            """
            DELETE
            FROM storage_boxes
            WHERE id = ?
            """,
            (box_id,)
        )

        self.conn.commit()


    def get_box(self, box_id):

        cursor = self.conn.execute(
            """
            SELECT *
            FROM storage_boxes
            WHERE id = ?
            """,
            (box_id,)
        )

        return cursor.fetchone()


    def get_box_by_name(self, box_name):

        cursor = self.conn.execute(
            """
            SELECT *
            FROM storage_boxes
            WHERE box_name = ?
            """,
            (box_name,)
        )

        return cursor.fetchone()


    def list_boxes(self):

        cursor = self.conn.execute(
            """
            SELECT

                b.id,
                b.box_name,
                b.box_type,
                b.owner,
                b.shelf,
                b.slot,
                b.notes,

                r.rack_name,
                r.rack_type

            FROM storage_boxes b

            JOIN storage_racks r

                ON b.rack_id = r.id
            """
        )

        return cursor.fetchall()


    def move_box(
        self,
        box_id,
        rack_id,
        shelf,
        slot
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

    def create_positions(
        self,
        box_id,
        box_type
    ):

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

                positions.append(
                    (
                        box_id,
                        f"{row}{col}"
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


    def list_positions(
        self,
        box_id
    ):

        cursor = self.conn.execute(
            """
            SELECT

                p.id,
                p.position,

                c.id AS container_id,
                c.label,
                c.container_type

            FROM storage_positions p

            LEFT JOIN storage_containers c

                ON p.id = c.position_id

            WHERE p.box_id = ?

            ORDER BY p.position
            """,
            (box_id,)
        )

        return cursor.fetchall()


    def get_position(
        self,
        position_id
    ):

        cursor = self.conn.execute(
            """
            SELECT *

            FROM storage_positions

            WHERE id = ?
            """,
            (position_id,)
        )

        return cursor.fetchone()


    def get_position_by_name(
        self,
        box_id,
        position
    ):

        cursor = self.conn.execute(
            """
            SELECT *

            FROM storage_positions

            WHERE
                box_id = ?
                AND position = ?
            """,
            (
                box_id,
                position
            )
        )

        return cursor.fetchone()


    def list_free_positions(
        self,
        box_id
    ):

        cursor = self.conn.execute(
            """
            SELECT

                p.id,
                p.position

            FROM storage_positions p

            LEFT JOIN storage_containers c

                ON p.id = c.position_id

            WHERE

                p.box_id = ?

                AND c.id IS NULL

            ORDER BY p.position
            """,
            (box_id,)
        )

        return cursor.fetchall()


    def list_occupied_positions(
        self,
        box_id
    ):

        cursor = self.conn.execute(
            """
            SELECT

                p.position,

                c.id,
                c.label,
                c.container_type

            FROM storage_positions p

            JOIN storage_containers c

                ON p.id = c.position_id

            WHERE

                p.box_id = ?

            ORDER BY p.position
            """,
            (box_id,)
        )

        return cursor.fetchall()

        # =====================================================
    # CONTAINERS
    # =====================================================

    def create_container(
        self,
        position_id,
        container_type,
        label,
        notes=""
    ):

        cursor = self.conn.execute(
            """
            INSERT INTO storage_containers
            (
                position_id,
                container_type,
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
                position_id,
                container_type,
                label,
                notes
            )
        )

        self.conn.commit()

        return cursor.lastrowid


    def get_container(self, container_id):

        cursor = self.conn.execute(
            """
            SELECT *

            FROM storage_containers

            WHERE id = ?
            """,
            (container_id,)
        )

        return cursor.fetchone()


    def get_container_by_label(self, label):

        cursor = self.conn.execute(
            """
            SELECT *

            FROM storage_containers

            WHERE label = ?
            """,
            (label,)
        )

        return cursor.fetchone()


    def delete_container(self, container_id):

        self.conn.execute(
            """
            DELETE

            FROM storage_containers

            WHERE id = ?
            """,
            (container_id,)
        )

        self.conn.commit()


    def search_containers(self, text):

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

            WHERE

                c.label LIKE ?

            ORDER BY

                c.label
            """,
            (f"%{text}%",)
        )

        return cursor.fetchall()


    # =====================================================
    # DATABASE
    # =====================================================

    def commit(self):

        self.conn.commit()


    def rollback(self):

        self.conn.rollback()


    def close(self):

        self.conn.close()