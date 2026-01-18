FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install uv
RUN pip install uv

# Dependencies layer (cached unless pyproject.toml changes)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Production image
FROM base AS production
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "groundwork.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development image
FROM base AS development
RUN uv sync --frozen
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "groundwork.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
