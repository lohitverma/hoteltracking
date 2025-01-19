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
RUN mkdir -p /app/wheels && chown -R appuser:appuser /app /opt/venv

# Copy requirements and set ownership
COPY requirements.txt /app/
RUN chown appuser:appuser /app/requirements.txt

# Switch to non-root user
USER appuser

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Install core dependencies first
RUN pip wheel --no-deps --no-cache-dir --wheel-dir /app/wheels \
    anyio==3.7.1 \
    starlette==0.27.0 \
    typing-extensions==4.8.0 \
    idna==3.4 \
    sniffio==1.3.0 \
    pydantic-core==2.14.5

# Install remaining dependencies
RUN pip wheel --no-deps --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

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

# Set up directories
WORKDIR /app
RUN mkdir -p /app/wheels && chown -R appuser:appuser /app /opt/venv

# Copy wheels and requirements from builder
COPY --from=builder --chown=appuser:appuser /app/wheels /app/wheels
COPY --from=builder --chown=appuser:appuser /app/requirements.txt .

# Switch to non-root user
USER appuser

# Upgrade pip
RUN pip install --upgrade pip

# Install core dependencies first
RUN pip install --no-cache-dir \
    anyio==3.7.1 \
    starlette==0.27.0 \
    typing-extensions==4.8.0 \
    idna==3.4 \
    sniffio==1.3.0 \
    pydantic-core==2.14.5

# Install remaining dependencies
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels -r requirements.txt && \
    rm -rf /app/wheels

# Copy application code
COPY --chown=appuser:appuser . .

# Create start script with health check
RUN echo '#!/bin/bash\n\
echo "Starting Hotel Tracker API..."\n\
echo "Environment: $ENVIRONMENT"\n\
echo "Allowed Hosts: $ALLOWED_HOSTS"\n\
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 4' > start.sh && \
    chmod +x start.sh

EXPOSE $PORT
CMD ["./start.sh"]
