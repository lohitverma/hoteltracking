FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip wheel --no-deps --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/backend \
    PORT=10000 \
    ENVIRONMENT=production \
    DEBUG=false \
    ALLOWED_HOSTS=".onrender.com"

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /app/wheels /app/wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels -r requirements.txt \
    && rm -rf /app/wheels

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Create start script with health check
RUN echo '#!/bin/bash\n\
echo "Starting Hotel Tracker API..."\n\
echo "Environment: $ENVIRONMENT"\n\
echo "Allowed Hosts: $ALLOWED_HOSTS"\n\
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 4' > start.sh && \
    chmod +x start.sh

EXPOSE $PORT
CMD ["./start.sh"]
