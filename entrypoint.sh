#!/bin/bash
set -e

echo "Starting application..."

# Set and export port
export PORT="${PORT:-10000}"
echo "PORT set to: $PORT"

# Start the application
echo "Starting FastAPI application on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
