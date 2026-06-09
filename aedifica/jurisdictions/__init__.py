"""Country/canton/commune jurisdiction lookups.

The resolver takes a free-text commune name + a country code and returns the
canton (or cantons, for homonyms). Switzerland is the only country wired up
today; the module is structured so that more countries can be plugged in
without touching consumers — every resolver returns the same shape.

Doctrine: never invent a canton. When the commune is unknown to the curated
dataset, the resolver returns ``confidence="unknown"`` with the full canton
list as candidates, so the UI can ask the user. When the same name maps to
several cantons (real Swiss homonyms: Wald, Buchs, Reinach, …), the resolver
returns ``confidence="ambiguous"`` with the matching candidates.
"""

from .resolver import resolve, list_countries, list_regions, freshness

__all__ = ["resolve", "list_countries", "list_regions", "freshness"]
