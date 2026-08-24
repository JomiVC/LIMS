"""
services/container_detail_bootstrap.py

Explicit, single entry point for registering every
ContainerDetailProvider with services.container_detail_registry.

Call bootstrap_container_detail_providers() once, early, from the
app's entry point (e.g. app.py) -- before any page calls
StorageService.get_container_details. This is the one place that
lists every domain module contributing a provider; registration
never happens as a side effect of importing a provider module.

To add a new domain (DNA, Reagents, ...):
1. Give that module a register_xxx_providers() function, analogous
   to register_protein_providers() in
   protein_container_detail_provider.py.
2. Import it below and call it inside
   bootstrap_container_detail_providers().
"""

from services.protein_container_detail_provider import (
    register_protein_providers,
)


def bootstrap_container_detail_providers() -> None:
    """
    Registers every known ContainerDetailProvider. Meant to run once
    at app startup; calling it again just re-registers the same
    providers (register_provider overwrites by key), so it's
    harmless but unnecessary to call more than once.
    """

    register_protein_providers()

    # Add future domains here, e.g.:
    # register_dna_providers()
    # register_reagent_providers()