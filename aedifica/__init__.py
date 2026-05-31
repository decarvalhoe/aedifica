"""Aedifica — product package exposing a stable namespace over the pilot services.

The stdlib implementation currently lives in ``pilot/`` (exercised by
``pilot/selfcheck.py`` and the CI contract validators). This package is the
public import surface that the workspace API, UI and future adapters depend on,
so they never import pilot scripts directly.

See docs/architecture/package-boundaries.md for the module boundaries.
"""
from __future__ import annotations

from . import _bootstrap  # noqa: F401  (side effect: puts pilot/ on sys.path)

__version__ = "0.1.0"
SCHEMA_VERSION = "1.0"

from . import claims, domain, evidence, route, workspace  # noqa: E402

__all__ = [
    "__version__",
    "SCHEMA_VERSION",
    "claims",
    "domain",
    "evidence",
    "route",
    "workspace",
]
