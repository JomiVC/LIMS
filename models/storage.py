"""
models/storage.py

Storage Domain Models

Dataclasses that represent the storage hierarchy:
Freezer -> Rack -> Box -> Position -> Container

These are plain data objects (no DB access here). The repository
is responsible for building these from sqlite3.Row and for
converting them back to primitives when writing to the DB.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sqlite3


# ==========================================================
# FREEZER
# ==========================================================

@dataclass
class Freezer:

    id: Optional[int]
    name: str
    temperature: Optional[float]
    description: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Freezer":
        return cls(
            id=row["id"],
            name=row["name"],
            temperature=row["temperature"],
            description=row["description"],
        )


# ==========================================================
# RACK
# ==========================================================

@dataclass
class Rack:

    id: Optional[int]
    freezer_id: int
    rack_name: str
    rack_type: str  # 'EPPENDORF' | 'FALCON'
    has_shelf: bool
    slot_count: int
    description: Optional[str]

    def __post_init__(self) -> None:
        if self.rack_type not in ("EPPENDORF", "FALCON"):
            raise ValueError(f"Invalid rack_type: {self.rack_type}")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Rack":
        return cls(
            id=row["id"],
            freezer_id=row["freezer_id"],
            rack_name=row["rack_name"],
            rack_type=row["rack_type"],
            has_shelf=bool(row["has_shelf"]),
            slot_count=row["slot_count"],
            description=row["description"],
        )


# ==========================================================
# BOX
# ==========================================================

@dataclass
class Box:

    id: Optional[int]
    box_name: str
    legacy_name: Optional[str]
    box_type: str  # 'EPPENDORF' | 'FALCON'
    owner: Optional[str]
    rack_id: int
    shelf: Optional[int]
    slot: int
    notes: Optional[str]
    active: bool = True

    def __post_init__(self) -> None:
        if self.box_type not in ("EPPENDORF", "FALCON"):
            raise ValueError(f"Invalid box_type: {self.box_type}")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Box":
        return cls(
            id=row["id"],
            box_name=row["box_name"],
            legacy_name=row["legacy_name"],
            box_type=row["box_type"],
            owner=row["owner"],
            rack_id=row["rack_id"],
            shelf=row["shelf"],
            slot=row["slot"],
            notes=row["notes"],
            active=bool(row["active"]),
        )


# ==========================================================
# POSITION
# ==========================================================

@dataclass
class Position:

    id: Optional[int]
    box_id: int
    position: str  # e.g. "A1"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Position":
        return cls(
            id=row["id"],
            box_id=row["box_id"],
            position=row["position"],
        )


# ==========================================================
# CONTAINER STATUS
# ==========================================================

CONTAINER_STATUSES = ("ACTIVE", "CONSUMED", "DISCARDED")

CONTAINER_TYPES = ("DNA", "PROTEIN_ALIQUOT", "REAGENT_LOT")


# ==========================================================
# CONTAINER
# ==========================================================

@dataclass
class Container:
    """
    A container occupies exactly one storage position and holds
    exactly one item, linked through one of dna_id /
    protein_aliquot_id / reagent_lot_id (matching container_type).

    Mirrors the CHECK constraints in storage_containers: exactly
    one item_id field is set, and it matches container_type.
    """

    id: Optional[int]
    container_type: str
    position_id: int
    label: Optional[str]
    dna_id: Optional[int] = None
    protein_aliquot_id: Optional[int] = None
    reagent_lot_id: Optional[int] = None
    status: str = "ACTIVE"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:

        if self.status not in CONTAINER_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")

        if self.container_type not in CONTAINER_TYPES:
            raise ValueError(
                f"Invalid container_type: {self.container_type}"
            )

        item_ids = (
            self.dna_id,
            self.protein_aliquot_id,
            self.reagent_lot_id,
        )

        set_count = sum(1 for v in item_ids if v is not None)

        if set_count != 1:
            raise ValueError(
                "Exactly one of dna_id / protein_aliquot_id / "
                f"reagent_lot_id must be set (got {set_count})."
            )

        expected = {
            "DNA": self.dna_id,
            "PROTEIN_ALIQUOT": self.protein_aliquot_id,
            "REAGENT_LOT": self.reagent_lot_id,
        }[self.container_type]

        if expected is None:
            raise ValueError(
                f"container_type='{self.container_type}' but its "
                f"matching id field is not set."
            )

    @property
    def item_id(self) -> int:
        """The id of the linked item, regardless of its type."""
        return (
            self.dna_id
            or self.protein_aliquot_id
            or self.reagent_lot_id
        )

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Container":
        return cls(
            id=row["id"],
            container_type=row["container_type"],
            position_id=row["position_id"],
            label=row["label"],
            dna_id=row["dna_id"],
            protein_aliquot_id=row["protein_aliquot_id"],
            reagent_lot_id=row["reagent_lot_id"],
            status=row["status"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
            notes=row["notes"],
        )


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)