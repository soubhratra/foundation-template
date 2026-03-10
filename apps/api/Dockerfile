# Multi-stage production Dockerfile for Django API
# Base image: Debian slim for wheel compatibility
# Final size target: ~150MB

# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for building Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies to /app/.venv
RUN uv venv /app/.venv && \
    uv pip install --no-cache -r pyproject.toml

# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only (postgres client, not build tools)
# WeasyPrint system deps: pango (font/text rendering), gdk-pixbuf (image support),
# libffi (cffi bindings), shared-mime-info (MIME type detection)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi8 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health/', timeout=5)"

# Run gunicorn (production WSGI server)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "config.wsgi:application"]
