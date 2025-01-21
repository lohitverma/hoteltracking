#!/bin/bash
set -e

echo "Starting application initialization..."

# Function to get database connection parameters from DATABASE_URL or individual vars
get_db_params() {
    if [ ! -z "$DATABASE_URL" ]; then
        # Extract components from DATABASE_URL
        if [[ "$DATABASE_URL" =~ ^postgres(ql)?://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)$ ]]; then
            echo "${BASH_REMATCH[2]} ${BASH_REMATCH[3]} ${BASH_REMATCH[4]} ${BASH_REMATCH[5]} ${BASH_REMATCH[6]}"
        else
            echo "Invalid DATABASE_URL format"
            exit 1
        fi
    else
        # Use individual environment variables
        echo "$POSTGRES_USER $POSTGRES_PASSWORD $POSTGRES_HOST $POSTGRES_PORT $POSTGRES_DB"
    fi
}

# Get database parameters
read DB_USER DB_PASSWORD DB_HOST DB_PORT DB_NAME <<< $(get_db_params)

echo "Waiting for database to be ready..."
# Wait for database to be ready
MAX_RETRIES=60
RETRY_INTERVAL=5
RETRY_COUNT=0

until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Error: Could not connect to PostgreSQL after $MAX_RETRIES attempts"
        echo "Database Host: $DB_HOST"
        echo "Database Port: $DB_PORT"
        echo "Database Name: $DB_NAME"
        echo "Database User: $DB_USER"
        exit 1
    fi
    echo "PostgreSQL is unavailable - sleeping for $RETRY_INTERVAL seconds (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

echo "PostgreSQL is ready!"

# Initialize Alembic if not already initialized
if [ ! -d "migrations" ]; then
    echo "Initializing Alembic..."
    alembic init migrations
fi

# Create versions directory if it doesn't exist
mkdir -p migrations/versions

# Generate initial migration if no migrations exist
if [ ! "$(ls -A migrations/versions)" ]; then
    echo "Generating initial migration..."
    alembic revision --autogenerate -m "Initial migration"
fi

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Start the application
echo "Starting the application..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 --log-level info
