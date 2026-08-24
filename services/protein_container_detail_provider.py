"""
services/protein_container_detail_provider.py

Protein's item-detail rendering, registered against the generic
Storage registry (services/container_detail_registry.py) so
StorageService never needs to import ProteinRepository directly.

Registration is explicit: call register_protein_providers() -- do
not rely on importing this module for its side effect. It's called
from services/container_detail_bootstrap.py, the single place that
wires up every domain's providers at app startup.
"""

from repositories.protein_repository import ProteinRepository
from services.container_detail_registry import register_provider


"""
services/protein_container_detail_provider.py

Protein's item-detail rendering, registered against the generic
Storage registry (services/container_detail_registry.py) so
StorageService never needs to import ProteinRepository directly.

Registration is explicit: call register_protein_providers() -- do
not rely on importing this module for its side effect. It's called
from services/container_detail_bootstrap.py, the single place that
wires up every domain's providers at app startup.

Also exposes format_sample_label(), the single source of truth for
the enriched sample identifier ('Sample ID | Protein | Construct |
Variant | Media') shown in both pages/proteins.py and
pages/storage.py. It lives here rather than in either page module
because a Streamlit page script can't be safely imported by another
page (importing it re-executes its top-level UI code); this
services module can be imported by both without side effects.
"""

from repositories.protein_repository import ProteinRepository
from services.container_detail_registry import register_provider


def format_sample_label(record) -> str:
    """
    Formats a protein record (expressed or purified) as
    'Sample ID | Protein | Construct | Variant | Media', e.g.
    'S017 | p53 | pET28a | WT | 15N'. Falls back to the numeric id
    when sample_id is missing, and to '-' for any other missing
    field.
    """

    sample_id = record.sample_id or str(record.id)
    protein_name = record.protein_name or "-"
    construct = record.construct or "-"
    variant = record.variant or "-"
    media = record.media or "-"

    return f"{sample_id} | {protein_name} | {construct} | {variant} | {media}"


class _ProteinExpressedDetailProvider:

    def __init__(self):
        self._repo = ProteinRepository()

    def get_details(self, item_id):

        item = self._repo.get_expressed(item_id)

        if not item:
            return None

        details = {
            "🔖 Sample ID": item.sample_id,
            "🧬 Protein": item.protein_name,
            "🔨 Construct": item.construct or "—",
            "🔄 Variant": item.variant or "—",
            "🥛 Media": item.media or "—",
            "📦 Batch": item.batch_no or "—",
            "📊 Vol/Falcon (L)": item.volume_per_falcon_l or "—",
            "🧪 Buffer": item.buffer or "—",
            "📅 Date Stored": item.date_stored or "—",
            "📔 Notebook Ref": item.notebook_ref or "—",
            "🔢 Total Falcons": item.total_falcons,
            "📝 Notes": item.notes or "—",
        }

        return item.protein_name, details


class _ProteinPurifiedDetailProvider:

    def __init__(self):
        self._repo = ProteinRepository()

    def get_details(self, item_id):

        item = self._repo.get_purified(item_id)

        if not item:
            return None

        details = {
            "🔖 Sample ID": item.sample_id,
            "🧬 Protein": item.protein_name,
            "🔨 Construct": item.construct or "—",
            "🔄 Variant": item.variant or "—",
            "🥛 Media": item.media or "—",
            "📦 Batch": item.batch_no or "—",
            "📐 Concentration (µM)": item.concentration_um or "—",
            "💧 Volume (µL)": item.volume_ul or "—",
            "🧪 Buffer": item.buffer or "—",
            "📅 Date Stored": item.date_stored or "—",
            "📔 Notebook Ref": item.notebook_ref or "—",
            "🔢 Total Aliquots": item.total_aliquots,
            "📝 Notes": item.notes or "—",
        }

        return item.protein_name, details


def register_protein_providers() -> None:
    """
    Registers every Protein ContainerDetailProvider. Called
    explicitly by container_detail_bootstrap -- must not run as an
    import side effect.
    """

    register_provider(
        "PROTEIN_EXPRESSED", _ProteinExpressedDetailProvider()
    )
    register_provider(
        "PROTEIN_PURIFIED", _ProteinPurifiedDetailProvider()
    )