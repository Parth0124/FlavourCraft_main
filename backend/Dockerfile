# Multi-stage Dockerfile for FlavourCraft Backend
# Stage 1: Build stage for dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies required to compile wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create a venv and install packages into it (robust pip options)
RUN python -m venv /opt/venv \
 && /opt/venv/bin/python -m pip install --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip --disable-pip-version-check --default-timeout=120 --retries=5 --no-cache-dir install -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

WORKDIR /app

# Runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from builder
COPY --from=builder /opt/venv /opt/venv

# Put venv's bin first in PATH so uvicorn and other scripts are found
ENV PATH="/opt/venv/bin:${PATH}"

# Copy application code
COPY . .

# Create necessary directories (absolute paths) and set ownership
RUN mkdir -p /app/uploads /app/temp /app/logs /app/mlruns \
 && useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app /opt/venv /app/uploads /app/temp /app/logs /app/mlruns || true

# Switch to non-root user
USER appuser

# Default port for local testing; platforms will override PORT env var at runtime
ENV PORT=8000
EXPOSE ${PORT}

# Health check uses the same PORT env var
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD sh -c "curl -f http://localhost:${PORT}/health || exit 1"

# Run the application via the venv-installed uvicorn and use the PORT env var
# Use sh -c so ${PORT} expands inside the container
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
