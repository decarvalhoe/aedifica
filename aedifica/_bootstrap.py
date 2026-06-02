"""Single coupling point between the `aedifica` product package and `pilot/`.

The stdlib implementation currently lives in `pilot/` and is exercised by
`pilot/selfcheck.py` plus the CI contract validators. Putting it on `sys.path`
here lets the product package re-export it as a stable namespace without copying
logic. See docs/architecture/package-boundaries.md.
"""
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PILOT_DIR = os.path.join(REPO_ROOT, "pilot")

if PILOT_DIR not in sys.path:
    sys.path.insert(0, PILOT_DIR)
