"""Aedifica product HTTP API (FastAPI over the engine + SQL store).

Requires the ``product`` optional dependencies (fastapi, sqlalchemy). The offline
engine stays stdlib-only and is not imported by ``aedifica`` core.
"""
from __future__ import annotations

from .app import create_app

__all__ = ["create_app"]
