# Aedifica product API (FastAPI over the engine + SQL).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AEDIFICA_ENV=prod

COPY pyproject.toml alembic.ini ./
COPY aedifica ./aedifica
COPY pilot ./pilot
COPY tests/contracts ./tests/contracts

RUN pip install -e ".[product]"

EXPOSE 8090

# Apply migrations, then serve.
CMD ["sh", "-c", "alembic upgrade head && uvicorn aedifica.api.app:app --host 0.0.0.0 --port 8090"]
