#!/bin/bash
echo "Starting Hotel Tracker API..."
echo "Environment: $ENVIRONMENT"
echo "Allowed Hosts: $ALLOWED_HOSTS"
echo "Port: ${PORT:-8000}"

# Wait for port to be available
timeout=30
counter=0
while ! nc -z localhost ${PORT:-8000} 2>/dev/null; do
    if [ $counter -gt $timeout ]; then
        echo "Timeout waiting for port ${PORT:-8000} to be available"
        exit 1
    fi
    sleep 1
    ((counter++))
done

# Start the application
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4
