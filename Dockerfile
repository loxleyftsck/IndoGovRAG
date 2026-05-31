# =============================================================================
# Multi-stage Docker build for IndoGovRAG
# Production-optimized with security hardening
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install Python dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (gcc, libs for native extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching: only rebuild if deps change)
COPY requirements.txt .

# Install Python packages into isolated user location
RUN pip install --no-cache-dir --user -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production runtime - Minimal, non-root
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime-only dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated app user (non-root security)
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup api/ ./api/
COPY --chown=appuser:appgroup data/ ./data/
COPY --chown=appuser:appgroup config/ ./config/
COPY --chown=appuser:appgroup .env.example .env.example

# Create runtime directories
RUN mkdir -p data/vector_db/chroma \
             data/evaluations \
             logs \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Expose API port
EXPOSE 8000

# Health check - verify /health endpoint responds
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# Run API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Stage 3: Development (optional target)
# =============================================================================
FROM builder AS development

USER root

# Copy all project files
COPY . .

# Install dev dependencies
RUN pip install --no-cache-dir --user -r requirements.txt -r requirements-dev.txt

USER appuser

ENV ENVIRONMENT=development

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Build dev image: docker build --target development -t indogovrag:dev .