# Product test suite (DB + API)

Tests for the deployed product stack (ADR-0002): SQLAlchemy models, persistence
repositories, the FastAPI API, and on-demand commune ingestion. Unlike the
offline engine (`pilot/selfcheck.py`, stdlib-only), these require the `product`
and `test` optional dependencies.

```bash
pip install -e ".[product,test]"

# Run the product suite
python -m pytest tests/product -q

# Verify the Alembic baseline applies on a clean SQLite db
AEDIFICA_DATABASE_URL=sqlite:///dev.db python -m alembic upgrade head

# Run the API locally
AEDIFICA_CREATE_ALL=1 uvicorn aedifica.api.app:app --reload
```

## Parity

CI runs **two jobs** (`.github/workflows/ci.yml`):
- `pilot` — the stdlib offline engine (validators + selfcheck), no dependencies;
- `product` — installs the product deps, applies the migration, runs this suite,
  and re-checks the offline engine.

Both must stay green (the W1 CI parity gate, AED-131/#170).
