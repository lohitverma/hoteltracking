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

# Set working directory
WORKDIR /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/backend \
    PORT=10000 \
    VIRTUAL_ENV=/opt/venv

# Install runtime dependencies including PostgreSQL client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser

# Set up directories and permissions
WORKDIR /app
RUN mkdir -p /opt/venv /app/migrations/versions && \
    chown -R appuser:appuser /opt/venv /app

# Create virtual environment
RUN python -m venv $VIRTUAL_ENV && \
    chown -R appuser:appuser $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy virtual environment and application files
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser . .

# Set file permissions
RUN chmod +x start.sh && \
    chmod -R 755 migrations

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE ${PORT}

# Start the application
CMD ["./start.sh"]
