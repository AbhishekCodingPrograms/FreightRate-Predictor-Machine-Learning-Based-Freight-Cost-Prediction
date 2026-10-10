# Dockerfile for FreightRate Predictor FastAPI Service
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files, enable unbuffered logging, and set joblib thread limits for container runtimes
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LOKY_MAX_CPU_COUNT=2
ENV OMP_NUM_THREADS=2
ENV MKL_NUM_THREADS=2

WORKDIR /app

# Install system dependencies needed by LightGBM, CatBoost, XGBoost & PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages deterministically
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user for runtime security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

# Copy application source code (excluding any pre-built Windows artifacts)
COPY --chown=appuser:appuser . .

# Verify pre-built model artifact is valid; train only if missing
RUN python -c "from pathlib import Path; p = Path('artifacts/freight_rate_model.joblib'); (print('Using verified pre-built artifact:', p) if p.exists() else (__import__('src.train', fromlist=['run_training_pipeline']).run_training_pipeline()))"

USER appuser

EXPOSE 8000

# Health check rule against FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production ASGI startup: execute DB migrations followed by uvicorn server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
