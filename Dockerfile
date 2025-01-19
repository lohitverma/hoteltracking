FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend \
    PORT=10000 \
    ENVIRONMENT=production \
    DEBUG=false \
    ALLOWED_HOSTS=".onrender.com"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE $PORT

# Create start script
RUN echo '#!/bin/bash\nuvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 4' > start.sh && \
    chmod +x start.sh

# Default command
CMD ["./start.sh"]
