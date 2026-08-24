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