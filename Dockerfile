FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/backend \
    VIRTUAL_ENV=/opt/venv

# Create virtual environment
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser

# Set working directory and change ownership
WORKDIR /app
COPY requirements.txt .
RUN chown -R appuser:appuser /app /opt/venv

# Switch to non-root user
USER appuser

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/backend \
    PORT=10000 \
    ENVIRONMENT=production \
    DEBUG=false \
    ALLOWED_HOSTS=".onrender.com" \
    VIRTUAL_ENV=/opt/venv

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Create non-root user
RUN useradd -m appuser

# Set up directories and copy files
WORKDIR /app
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Create start script
RUN echo '#!/bin/bash\n\
echo "Starting Hotel Tracker API..."\n\
echo "Environment: $ENVIRONMENT"\n\
echo "Allowed Hosts: $ALLOWED_HOSTS"\n\
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 4' > start.sh && \
    chmod +x start.sh

EXPOSE $PORT
CMD ["./start.sh"]
