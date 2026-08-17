"""
services/item_service.py

Business logic for the remaining item stub tables (DNA / reagent
lots). Proteins are no longer handled here -- they now have real
tables (protein_expressed, protein_purified) and will get their own
dedicated repository/service as part of the Proteins module.
"""

from repositories.item_repository import ItemRepository


CONTAINER_TYPE_LABELS = {
    "DNA": "DNA",
    "REAGENT_LOT": "Reagent lot",
}


class ItemService:

    def __init__(self):
        self.repository = ItemRepository()

    # =====================================================
    # DNA
    # =====================================================

    def list_dna(self):
        return self.repository.list_dna()

    def create_dna(self, name, notes=""):

        name = name.strip()

        if not name:
            raise ValueError("Name cannot be empty.")

        return self.repository.create_dna(name=name, notes=notes)

    # =====================================================
    # REAGENT LOTS
    # =====================================================

    def list_reagents(self):
        return self.repository.list_reagents()

    def create_reagent(self, name, notes=""):

        name = name.strip()

        if not name:
            raise ValueError("Name cannot be empty.")

        return self.repository.create_reagent(name=name, notes=notes)

    # =====================================================
    # GENERIC
    # =====================================================

    def list_items(self, container_type):
        """
        Returns the item list matching container_type
        ('DNA' | 'REAGENT_LOT').
        """

        if container_type == "DNA":
            return self.list_dna()

        if container_type == "REAGENT_LOT":
            return self.list_reagents()

        raise ValueError(f"Unknown container_type: {container_type}")

    def create_item(self, container_type, name, notes=""):
        """
        Creates an item of the given type and returns its id.
        """

        if container_type == "DNA":
            return self.create_dna(name, notes)

        if container_type == "REAGENT_LOT":
            return self.create_reagent(name, notes)

        raise ValueError(f"Unknown container_type: {container_type}")

    def get_item_name(self, container_type, item_id):
        return self.repository.get_item_name(container_type, item_id)