"""
models/protein.py

Domain models for the Proteins module.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sqlite3


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


@dataclass
class ProteinExpressed:

    id: Optional[int]
    sample_id: str
    protein_name: str
    construct: Optional[str]
    variant: Optional[str]
    media: Optional[str]
    batch_no: Optional[str]
    volume_per_falcon_l: Optional[float]
    buffer: Optional[str]
    date_stored: Optional[str]
    notebook_ref: Optional[str]
    total_falcons: int
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ProteinExpressed":
        return cls(
            id=row["id"],
            sample_id=row["sample_id"],
            protein_name=row["protein_name"],
            construct=row["construct"],
            variant=row["variant"],
            media=row["media"],
            batch_no=row["batch_no"],
            volume_per_falcon_l=row["volume_per_falcon_l"],
            buffer=row["buffer"],
            date_stored=row["date_stored"],
            notebook_ref=row["notebook_ref"],
            total_falcons=row["total_falcons"],
            notes=row["notes"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )


@dataclass
class ProteinPurified:

    id: Optional[int]
    sample_id: str
    protein_name: str
    construct: Optional[str]
    variant: Optional[str]
    media: Optional[str]
    batch_no: Optional[str]
    concentration_um: Optional[float]
    volume_ul: Optional[float]
    buffer: Optional[str]
    date_stored: Optional[str]
    notebook_ref: Optional[str]
    total_aliquots: int
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ProteinPurified":
        return cls(
            id=row["id"],
            sample_id=row["sample_id"],
            protein_name=row["protein_name"],
            construct=row["construct"],
            variant=row["variant"],
            media=row["media"],
            batch_no=row["batch_no"],
            concentration_um=row["concentration_um"],
            volume_ul=row["volume_ul"],
            buffer=row["buffer"],
            date_stored=row["date_stored"],
            notebook_ref=row["notebook_ref"],
            total_aliquots=row["total_aliquots"],
            notes=row["notes"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )