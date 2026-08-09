"""
services/item_service.py

Business logic for the item stub tables (DNA / protein aliquots /
reagent lots). Minimal on purpose -- replace with a dedicated
service per module (DnaService, ProteinService, ReagentService)
once each real module is built.
"""

from repositories.item_repository import ItemRepository


CONTAINER_TYPE_LABELS = {
    "DNA": "DNA",
    "PROTEIN_ALIQUOT": "Protein aliquot",
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
    # PROTEIN ALIQUOTS
    # =====================================================

    def list_proteins(self):
        return self.repository.list_proteins()

    def create_protein(self, name, notes=""):

        name = name.strip()

        if not name:
            raise ValueError("Name cannot be empty.")

        return self.repository.create_protein(name=name, notes=notes)

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
        ('DNA' | 'PROTEIN_ALIQUOT' | 'REAGENT_LOT').
        """

        if container_type == "DNA":
            return self.list_dna()

        if container_type == "PROTEIN_ALIQUOT":
            return self.list_proteins()

        if container_type == "REAGENT_LOT":
            return self.list_reagents()

        raise ValueError(f"Unknown container_type: {container_type}")

    def create_item(self, container_type, name, notes=""):
        """
        Creates an item of the given type and returns its id.
        """

        if container_type == "DNA":
            return self.create_dna(name, notes)

        if container_type == "PROTEIN_ALIQUOT":
            return self.create_protein(name, notes)

        if container_type == "REAGENT_LOT":
            return self.create_reagent(name, notes)

        raise ValueError(f"Unknown container_type: {container_type}")

    def get_item_name(self, container_type, item_id):
        return self.repository.get_item_name(container_type, item_id)