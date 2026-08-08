"""
services/storage_service.py

Business logic for the Storage module.
"""

from repositories.storage_repository import StorageRepository


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

        rack_name = rack["rack_name"]

        if rack_name in ("A", "B", "C", "D"):

            return {
                "rack_id": rack["id"],
                "rack_name": rack_name,
                "rack_type": rack["rack_type"],
                "has_shelf": True,
                "shelves": [
                    "Upper",
                    "Lower"
                ],
                "slots": [1, 2, 3, 4, 5]
            }

        return {
            "rack_id": rack["id"],
            "rack_name": rack_name,
            "rack_type": rack["rack_type"],
            "has_shelf": False,
            "shelves": [],
            "slots": [1, 2, 3, 4, 5]
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

        existing = self.repository.get_box_by_name(box_name)

        if existing:

            raise ValueError(
                f"A box named '{box_name}' already exists."
            )

        config = self.get_rack_configuration(rack_id)

        if config["has_shelf"]:

            if shelf not in ("Upper", "Lower"):

                raise ValueError(
                    "Shelf must be 'Upper' or 'Lower'."
                )

        else:

            shelf = None

        if slot not in config["slots"]:

            raise ValueError(
                "Invalid slot."
            )

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
            box_id,
            box_type
        )

        return box_id


    def move_box(
        self,
        box_id,
        rack_id,
        shelf,
        slot
    ):

        config = self.get_rack_configuration(rack_id)

        if config["has_shelf"]:

            if shelf not in ("Upper", "Lower"):

                raise ValueError(
                    "Invalid shelf."
                )

        else:

            shelf = None

        if slot not in config["slots"]:

            raise ValueError(
                "Invalid slot."
            )

        self.repository.move_box(
            box_id,
            rack_id,
            shelf,
            slot
        )


    def delete_box(self, box_id):

        self.repository.delete_box(box_id)
    
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
        label,
        notes=""
    ):

        label = label.strip().upper()

        if not label:

            raise ValueError(
                "Container label cannot be empty."
            )

        existing = self.repository.get_container_by_label(label)

        if existing:

            raise ValueError(
                f"Container '{label}' already exists."
            )

        return self.repository.create_container(
            position_id=position_id,
            container_type=container_type,
            label=label,
            notes=notes
        )


    def get_container(self, container_id):

        container = self.repository.get_container(container_id)

        if container is None:

            raise ValueError("Container not found.")

        return container


    def search_containers(self, text):

        return self.repository.search_containers(text)


    def delete_container(self, container_id):

        self.repository.delete_container(container_id)


    # =====================================================
    # DATABASE
    # =====================================================

    def close(self):

        self.repository.close()
        