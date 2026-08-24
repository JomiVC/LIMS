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
from repositories.attachment_repository import AttachmentRepository


class StorageService:

    def __init__(self):

        self.repository = StorageRepository()
        self.attachment_repository = AttachmentRepository()

    # =====================================================
    # RACKS
    # =====================================================

    # =====================================================
    # FREEZERS
    # =====================================================

    def list_freezers(self):
        return self.repository.list_freezers()

    def get_freezer(self, freezer_id):

        freezer = self.repository.get_freezer(freezer_id)

        if freezer is None:
            raise ValueError("Freezer not found.")

        return freezer

    def create_freezer(self, name, temperature=None, description=""):

        name = name.strip()

        if not name:
            raise ValueError("Freezer name cannot be empty.")

        try:
            return self.repository.create_freezer(
                name=name,
                temperature=temperature,
                description=description,
            )
        except StorageError as e:
            raise ValueError(str(e)) from e

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

    # Which box types are physically compatible with each rack type.
    # FALCON racks (A-D) hold both Falcon tube sizes; EPPENDORF racks
    # (1-40) only hold EPPENDORF boxes.
    ALLOWED_BOX_TYPES_BY_RACK_TYPE = {
        "EPPENDORF": ["EPPENDORF"],
        "FALCON": ["FALCON_15", "FALCON"],
    }

    def get_rack_configuration(self, rack_id):

        rack = self.get_rack(rack_id)

        return {
            "rack_id": rack.id,
            "rack_name": rack.rack_name,
            "rack_type": rack.rack_type,
            "has_shelf": rack.has_shelf,
            "shelves": ["Upper", "Lower"] if rack.has_shelf else [],
            "slots": list(range(1, rack.slot_count + 1)),
            "allowed_box_types": self.ALLOWED_BOX_TYPES_BY_RACK_TYPE[
                rack.rack_type
            ],
        }

    def create_rack(
        self,
        freezer_id,
        rack_name,
        rack_type,
        has_shelf,
        slot_count,
        description=""
    ):
        """
        Not yet used by any page -- exposed so a future Rack
        management UI can call it without touching this layer.
        """

        rack_name = rack_name.strip()

        if not rack_name:
            raise ValueError("Rack name cannot be empty.")

        if rack_type not in ("EPPENDORF", "FALCON"):
            raise ValueError("Invalid rack type.")

        if slot_count < 1:
            raise ValueError("Slot count must be at least 1.")

        try:
            return self.repository.create_rack(
                freezer_id=freezer_id,
                rack_name=rack_name,
                rack_type=rack_type,
                has_shelf=has_shelf,
                slot_count=slot_count,
                description=description,
            )
        except StorageError as e:
            raise ValueError(str(e)) from e

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

        if box_type not in ("EPPENDORF", "FALCON", "FALCON_15"):
            raise ValueError("Invalid box type.")

        config = self.get_rack_configuration(rack_id)

        if box_type not in config["allowed_box_types"]:
            raise ValueError(
                f"Box type '{box_type}' cannot be placed in a "
                f"{config['rack_type']} rack ('{config['rack_name']}')."
            )

        if config["has_shelf"]:
            if shelf not in ("Upper", "Lower"):
                raise ValueError("Shelf must be 'Upper' or 'Lower'.")
        else:
            shelf = None

        if slot not in config["slots"]:
            raise ValueError("Invalid slot.")

        try:
            # Box + positions are created in a single SQLite
            # transaction (see StorageRepository.create_box_with_positions):
            # either both are committed or neither is, so there's no
            # window where a box exists without its positions.
            box_id = self.repository.create_box_with_positions(
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

    def get_position_by_name(self, box_id, position_name):

        return self.repository.get_position_by_name(box_id, position_name)

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

    def get_container_for_item(self, container_type, item_id):
        return self.repository.get_container_for_item(
            container_type, item_id
        )

    def search_containers(self, text):

        return self.repository.search_containers(text)

    def delete_container(self, container_id):

        self.repository.delete_container(container_id)

    # =====================================================
    # CONTAINER DETAILS (enriched with item info)
    # =====================================================

    def get_container_details(self, container_id):
        """
        Returns enriched container info including item name and
        attachments. Useful for displaying in UI modals.

        Item-specific rendering (e.g. for PROTEIN_EXPRESSED /
        PROTEIN_PURIFIED) is delegated to whatever provider the
        owning module registered in container_detail_registry --
        StorageService itself has no knowledge of Protein, DNA, or
        Reagents specifics.
        """
        from services.container_detail_registry import get_provider

        container = self.get_container(container_id)
        
        if not container:
            return None
        
        details = {
            "id": container.id,
            "container_id": container.id,
            "label": container.label,
            "container_type": container.container_type,
            "item_name": None,
            "item_id": None,
            "item_details": {},
            "attachments": [],
        }
        
        # Map container_type to attribute name and table name
        type_mapping = {
            "PROTEIN_EXPRESSED": ("protein_expressed_id", "protein_expressed"),
            "PROTEIN_PURIFIED": ("protein_purified_id", "protein_purified"),
            "DNA": ("dna_id", "dna_stock"),
            "REAGENT_LOT": ("reagent_lot_id", "reagent_lots"),
        }
        
        if container.container_type in type_mapping:
            attr_name, table_name = type_mapping[container.container_type]
            item_id = getattr(container, attr_name, None)
            
            if item_id:
                details["item_id"] = item_id

                provider = get_provider(container.container_type)

                if provider:
                    result = provider.get_details(item_id)

                    if result:
                        details["item_name"], details["item_details"] = (
                            result
                        )

                # Get attachments
                attachments = self.attachment_repository.list_for(
                    table_name, item_id
                )
                details["attachments"] = [dict(att) for att in attachments]
        
        return details