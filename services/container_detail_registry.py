"""
services/container_detail_registry.py

Generic registry that lets other domain modules (Protein, DNA,
Reagents, ...) plug in how to render their item's details inside a
storage container, without StorageService needing to import those
modules directly.

This inverts the Storage -> Protein dependency: instead of Storage
importing ProteinRepository, the Protein module imports
`register_provider` from here and registers itself. Storage only
depends on this generic contract, which lives in the Storage layer.

Registration is explicit, not an import side effect: each owning
module exposes a `register_xxx_providers()` function (see
services/protein_container_detail_provider.py) instead of calling
`register_provider(...)` at module import time, and
services/container_detail_bootstrap.py is the single place that
calls all of them. Call
`container_detail_bootstrap.bootstrap_container_detail_providers()`
once from the app's entry point, before any page calls
StorageService.get_container_details.
"""

from typing import Protocol


class ContainerDetailProvider(Protocol):
    """
    Implemented by any module that wants StorageService's
    get_container_details to be able to render its items
    (e.g. Protein, DNA, Reagents).
    """

    def get_details(self, item_id: int):
        """
        Returns (item_name, item_details_dict) for the given item_id,
        or None if the item doesn't exist.
        """
        ...


_PROVIDERS: dict[str, ContainerDetailProvider] = {}


def register_provider(
    container_type: str,
    provider: ContainerDetailProvider
) -> None:
    """
    Registers `provider` as the source of item details for
    `container_type` (e.g. 'PROTEIN_EXPRESSED'). Called by the owning
    module, not by Storage.
    """

    _PROVIDERS[container_type] = provider


def get_provider(container_type: str) -> ContainerDetailProvider | None:

    return _PROVIDERS.get(container_type)