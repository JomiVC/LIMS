"""
services/storage_service.py

Business logic for the Storage Engine.
"""

from repositories.storage_repository import StorageRepository


class StorageService:

    def __init__(self):

        self.repository = StorageRepository()

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

        box_name = box_name.strip()

        if not box_name:
            raise ValueError("Box name cannot be empty.")

        if box_type not in ("EPPENDORF", "FALCON"):
            raise ValueError("Invalid box type.")

        existing = self.repository.get_box_by_name(box_name)

        if existing:
            raise ValueError(f"Box '{box_name}' already exists.")

        box_id = self.repository.create_box(
            box_name=box_name,
            box_type=box_type,
            owner=owner,
            rack_id=rack_id,
            shelf=shelf,
            slot=slot,
            notes=notes
        )

        self.repository.create_positions(
            box_id=box_id,
            box_type=box_type
        )

        return box_id

    def list_boxes(self):

        return self.repository.list_boxes()

    def get_box(self, box_id: int):

        return self.repository.get_box(box_id)

    def move_box(
        self,
        box_id: int,
        rack_id: int,
        shelf: int,
        slot: int
    ):

        self.repository.move_box(
            box_id=box_id,
            rack_id=rack_id,
            shelf=shelf,
            slot=slot
        )

    def delete_box(self, box_id: int):

        self.repository.delete_box(box_id)

    # =====================================================
    # POSITIONS
    # =====================================================

    def list_positions(self, box_id: int):

        return self.repository.list_positions(box_id)

    # =====================================================
    # RACKS
    # =====================================================

    def list_racks(self):

        return self.repository.list_racks()

    # =====================================================
    # CLEANUP
    # =====================================================

    def close(self):

        self.repository.close()