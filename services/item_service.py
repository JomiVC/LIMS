"""
services/item_service.py

Business logic for the remaining item stub tables (DNA / reagent
lots). Proteins are no longer handled here -- they now have real
tables (protein_expressed, protein_purified) and will get their own
dedicated repository/service as part of the Proteins module.
"""

from repositories.item_repository import ItemRepository
from repositories.protein_repository import ProteinRepository


CONTAINER_TYPE_LABELS = {
    "DNA": "DNA",
    "PROTEIN_EXPRESSED": "Expressed protein",
    "PROTEIN_PURIFIED": "Purified protein",
    "REAGENT_LOT": "Reagent lot",
}


class ItemService:

    def __init__(self):
        self.repository = ItemRepository()
        self.protein_repository = ProteinRepository()

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
    # PROTEINS
    # =====================================================

    def list_expressed_proteins(self):
        """Returns list of expressed proteins in dict format for consistency."""
        proteins = self.protein_repository.list_expressed()
        return [
            {
                "id": p.id,
                "name": p.protein_name,
                "notes": p.notes or ""
            }
            for p in proteins
        ]

    def list_purified_proteins(self):
        """Returns list of purified proteins in dict format for consistency."""
        proteins = self.protein_repository.list_purified()
        return [
            {
                "id": p.id,
                "name": p.protein_name,
                "notes": p.notes or ""
            }
            for p in proteins
        ]

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
        ('DNA' | 'REAGENT_LOT' | 'PROTEIN_EXPRESSED' | 'PROTEIN_PURIFIED').
        """

        if container_type == "DNA":
            return self.list_dna()

        if container_type == "PROTEIN_EXPRESSED":
            return self.list_expressed_proteins()

        if container_type == "PROTEIN_PURIFIED":
            return self.list_purified_proteins()

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
        """Get item name for any container type."""
        if container_type == "PROTEIN_EXPRESSED":
            protein = self.protein_repository.get_expressed(item_id)
            return protein.protein_name if protein else None
        
        if container_type == "PROTEIN_PURIFIED":
            protein = self.protein_repository.get_purified(item_id)
            return protein.protein_name if protein else None
        
        return self.repository.get_item_name(container_type, item_id)