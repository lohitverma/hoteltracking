#!/bin/bash
echo "Starting Hotel Tracker API..."
echo "Environment: $ENVIRONMENT"
echo "Allowed Hosts: $ALLOWED_HOSTS"
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 4
