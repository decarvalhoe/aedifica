"""Live parcel pipeline: address/EGRID -> sourced brief, persistable to the store.

Reuses the stdlib engine (OEREB resolve + constraint/envelope claims) and falls
back to the offline Lausanne fixture when the live registries are unavailable.
"""
from __future__ import annotations

from .live import build_live_brief

__all__ = ["build_live_brief"]
