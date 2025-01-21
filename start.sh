#!/bin/bash
set -e

echo "Starting application initialization..."

# Function to parse DATABASE_URL
parse_db_url() {
    if [ -z "$DATABASE_URL" ]; then
        echo "ERROR: DATABASE_URL is not set"
        exit 1
    fi
    
    echo "Parsing DATABASE_URL..."
    
    # Extract components using pattern matching
    if [[ $DATABASE_URL =~ ^postgresql://([^:]+):([^@]+)@([^/]+)/(.+)$ ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASSWORD="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_NAME="${BASH_REMATCH[4]}"
        DB_PORT=5432
        
        export DB_USER DB_HOST DB_NAME DB_PORT
        
        echo "Successfully parsed database connection info:"
        echo "User: $DB_USER"
        echo "Host: $DB_HOST"
        echo "Database: $DB_NAME"
        echo "Port: $DB_PORT"
    else
        echo "ERROR: Invalid DATABASE_URL format"
        echo "Expected format: postgresql://user:password@host/dbname"
        exit 1
    fi
}

# Parse the database URL
parse_db_url

# Function to test PostgreSQL connection
test_postgres_connection() {
    echo "Testing PostgreSQL Connection..."
    
    # Test TCP connection
    echo "Testing TCP connection to $DB_HOST:$DB_PORT..."
    if nc -zv "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        echo "TCP connection successful"
    else
        echo "TCP connection failed"
        return 1
    fi
    
    # Test PostgreSQL connection
    echo "Testing PostgreSQL connection..."
    if PGPASSWORD="$DB_PASSWORD" psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME" -c "SELECT version();" >/dev/null 2>&1; then
        echo "PostgreSQL connection successful"
        return 0
    else
        echo "PostgreSQL connection failed"
        return 1
    fi
}

# Function to check basic connectivity
check_postgres() {
    if PGPASSWORD="$DB_PASSWORD" psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME" -c '\q' >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Wait for PostgreSQL server to be ready
MAX_RETRIES=60
RETRY_INTERVAL=5
RETRY_COUNT=0

until check_postgres; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Error: Could not connect to PostgreSQL server after $MAX_RETRIES attempts"
        echo "Final connection test results:"
        test_postgres_connection
        exit 1
    fi
    echo "PostgreSQL server is unavailable - sleeping for $RETRY_INTERVAL seconds (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

echo "PostgreSQL server is ready!"

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
PORT="${PORT:-10000}"
echo "Starting application on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 4 --log-level debug
