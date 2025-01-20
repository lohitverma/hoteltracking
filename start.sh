#!/bin/bash

# Apply database migrations
python -m alembic upgrade head

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT
