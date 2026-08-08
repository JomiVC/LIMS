"""
services/storage_service.py

Business logic for the Storage module.

All repository-level exceptions (RackNotFoundError,
BoxNotEmptyError, etc.) are caught here and re-raised as
ValueError, so callers (Streamlit pages) only ever need to
catch one exception type at this boundary.
"""

from repositories.storage_repository import (
    StorageRepository,
    StorageError,
)


class StorageService:

    def __init__(self):

        self.repository = StorageRepository()

    # =====================================================
    # RACKS
    # =====================================================

    def list_racks(self):

        return self.repository.list_racks()

    def get_rack(self, rack_id):

        rack = self.repository.get_rack(rack_id)

        if rack is None:
            raise ValueError("Rack not found.")

        return rack

    def get_rack_configuration(self, rack_id):

        rack = self.get_rack(rack_id)

        if rack.rack_name in ("A", "B", "C", "D"):

            return {
                "rack_id": rack.id,
                "rack_name": rack.rack_name,
                "rack_type": rack.rack_type,
                "has_shelf": True,
                "shelves": ["Upper", "Lower"],
                "slots": [1, 2, 3, 4, 5],
            }

        return {
            "rack_id": rack.id,
            "rack_name": rack.rack_name,
            "rack_type": rack.rack_type,
            "has_shelf": False,
            "shelves": [],
            "slots": [1, 2, 3, 4, 5],
        }

    # =====================================================
    # BOXES
    # =====================================================

    def list_boxes(self):

        return self.repository.list_boxes()

    def get_box(self, box_id):

        box = self.repository.get_box(box_id)

        if box is None:
            raise ValueError("Storage box not found.")

        return box

    def get_box_by_name(self, box_name):

        return self.repository.get_box_by_name(box_name)

    # =====================================================
    # CREATE / UPDATE / DELETE BOXES
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

        box_name = box_name.strip().upper()

        if not box_name:
            raise ValueError("Box name cannot be empty.")

        if box_type not in ("EPPENDORF", "FALCON"):
            raise ValueError("Invalid box type.")

        config = self.get_rack_configuration(rack_id)

        if config["has_shelf"]:
            if shelf not in ("Upper", "Lower"):
                raise ValueError("Shelf must be 'Upper' or 'Lower'.")
        else:
            shelf = None

        if slot not in config["slots"]:
            raise ValueError("Invalid slot.")

        try:
            box_id = self.repository.create_box(
                box_name=box_name,
                box_type=box_type,
                owner=owner,
                rack_id=rack_id,
                shelf=shelf,
                slot=slot,
                notes=notes
            )
        except StorageError as e:
            raise ValueError(str(e)) from e

        try:
            self.repository.create_positions(box_id, box_type)

        except StorageError as e:
            # Positions failed to create after the box succeeded --
            # remove the orphaned box rather than leaving a box with
            # no positions (each repository call is its own
            # transaction, so this isn't rolled back automatically).
            self.repository.delete_box(box_id)
            raise ValueError(
                f"Failed to create positions, box was rolled back: {e}"
            ) from e

        return box_id

    def update_box(self, box_id, rack_id, shelf, slot, owner, notes):
        """
        Full edit: location (rack/shelf/slot), owner, and notes.
        box_name and box_type are not editable here -- see
        StorageRepository.update_box for why.
        """

        config = self.get_rack_configuration(rack_id)

        if config["has_shelf"]:
            if shelf not in ("Upper", "Lower"):
                raise ValueError("Invalid shelf.")
        else:
            shelf = None

        if slot not in config["slots"]:
            raise ValueError("Invalid slot.")

        try:
            self.repository.update_box(
                box_id, rack_id, shelf, slot, owner, notes
            )
        except StorageError as e:
            raise ValueError(str(e)) from e

    def delete_box(self, box_id):

        try:
            self.repository.delete_box(box_id)
        except StorageError as e:
            raise ValueError(str(e)) from e

    # =====================================================
    # POSITIONS
    # =====================================================

    def list_positions(self, box_id):

        return self.repository.list_positions(box_id)

    def get_position(self, position_id):

        position = self.repository.get_position(position_id)

        if position is None:
            raise ValueError("Position not found.")

        return position

    def list_free_positions(self, box_id):

        return self.repository.list_free_positions(box_id)

    def list_occupied_positions(self, box_id):

        return self.repository.list_occupied_positions(box_id)

    # =====================================================
    # CONTAINERS
    # =====================================================

    def create_container(
        self,
        position_id,
        container_type,
        item_id,
        label,
        notes=""
    ):
        """
        `container_type` must be one of models.storage.CONTAINER_TYPES
        ('DNA' | 'PROTEIN_ALIQUOT' | 'REAGENT_LOT'), and `item_id`
        must reference an existing row in the matching item table.
        """

        label = label.strip().upper()

        if not label:
            raise ValueError("Container label cannot be empty.")

        existing = self.repository.get_container_by_label(label)

        if existing:
            raise ValueError(f"Container '{label}' already exists.")

        try:
            return self.repository.create_container(
                position_id=position_id,
                container_type=container_type,
                item_id=item_id,
                label=label,
                notes=notes
            )
        except StorageError as e:
            raise ValueError(str(e)) from e

    def get_container(self, container_id):

        container = self.repository.get_container(container_id)

        if container is None:
            raise ValueError("Container not found.")

        return container

    def search_containers(self, text):

        return self.repository.search_containers(text)

    def delete_container(self, container_id):

        self.repository.delete_container(container_id)

        