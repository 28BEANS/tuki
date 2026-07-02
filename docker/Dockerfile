# =============================================================================
# Tuki Backend — Dockerfile
# Multi-stage build for FastAPI with GDAL/GEOS support
# =============================================================================

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies for geo libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY apps/backend/pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# --- Stage 2: Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Install runtime geo libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal32 \
    libgeos-c1v5 \
    libproj25 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY apps/backend/app ./app
COPY packages/routing_engine ./routing_engine_pkg

# Install routing engine package
RUN pip install --no-cache-dir ./routing_engine_pkg

# Create non-root user
RUN useradd --create-home --shell /bin/bash tuki
USER tuki

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
