#!/bin/bash
set -e

echo "Starting application initialization..."

# Function to get database connection parameters from DATABASE_URL or individual vars
get_db_params() {
    local url=""
    if [ ! -z "$RENDER_INTERNAL_DATABASE_URL" ]; then
        url="$RENDER_INTERNAL_DATABASE_URL"
        echo "Using RENDER_INTERNAL_DATABASE_URL"
    elif [ ! -z "$DATABASE_URL" ]; then
        url="$DATABASE_URL"
        echo "Using DATABASE_URL"
    else
        echo "Using individual environment variables"
        echo "$POSTGRES_USER $POSTGRES_PASSWORD $POSTGRES_HOST $POSTGRES_PORT $POSTGRES_DB"
        return
    fi
    
    # Extract components from URL
    if [[ "$url" =~ ^postgres(ql)?://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)$ ]]; then
        echo "${BASH_REMATCH[2]} ${BASH_REMATCH[3]} ${BASH_REMATCH[4]} ${BASH_REMATCH[5]} ${BASH_REMATCH[6]}"
    else
        echo "Invalid database URL format"
        exit 1
    fi
}

# Get database parameters
read DB_USER DB_PASSWORD DB_HOST DB_PORT DB_NAME <<< $(get_db_params)

echo "Checking database connection..."

# Print Render environment information
echo "Render Environment Information:"
echo "RENDER_SERVICE_TYPE: $RENDER_SERVICE_TYPE"
echo "RENDER_SERVICE_NAME: $RENDER_SERVICE_NAME"
echo "RENDER_EXTERNAL_HOSTNAME: $RENDER_EXTERNAL_HOSTNAME"
echo "Database Host: $DB_HOST"
echo "Database Port: $DB_PORT"
echo "Database Name: $DB_NAME"

# Function to check if we can connect to PostgreSQL server
check_postgres() {
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c '\q' "sslmode=require" 2>/dev/null
    return $?
}

# Function to check if database exists
database_exists() {
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt "sslmode=require" | cut -d \| -f 1 | grep -qw "$DB_NAME"
    return $?
}

# Wait for PostgreSQL server to be ready
MAX_RETRIES=60
RETRY_INTERVAL=5
RETRY_COUNT=0

echo "Testing network connectivity..."
if command -v nc &> /dev/null; then
    nc -zv "$DB_HOST" "$DB_PORT" 2>&1 || echo "nc command failed"
fi

if command -v ping &> /dev/null; then
    ping -c 1 "$DB_HOST" || echo "ping command failed"
fi

if command -v dig &> /dev/null; then
    dig "$DB_HOST" || echo "dig command failed"
fi

echo "Network test complete."

until check_postgres; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Error: Could not connect to PostgreSQL server after $MAX_RETRIES attempts"
        echo "Database Host: $DB_HOST"
        echo "Database Port: $DB_PORT"
        echo "Database User: $DB_USER"
        echo "Environment Variables:"
        env | grep -i "database\|postgres\|render" | grep -v "password"
        exit 1
    fi
    echo "PostgreSQL server is unavailable - sleeping for $RETRY_INTERVAL seconds (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

echo "PostgreSQL server is ready!"

# Create database if it doesn't exist
if ! database_exists; then
    echo "Database $DB_NAME does not exist. Creating..."
    PGPASSWORD=$DB_PASSWORD createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    echo "Database $DB_NAME created successfully!"
else
    echo "Database $DB_NAME already exists."
fi

# Now wait for the specific database to be ready
echo "Checking database connection..."
RETRY_COUNT=0

until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' "sslmode=require" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Error: Could not connect to database $DB_NAME after $MAX_RETRIES attempts"
        echo "Database Host: $DB_HOST"
        echo "Database Port: $DB_PORT"
        echo "Database Name: $DB_NAME"
        echo "Database User: $DB_USER"
        echo "Environment Variables:"
        env | grep -i "database\|postgres\|render" | grep -v "password"
        exit 1
    fi
    echo "Database $DB_NAME is unavailable - sleeping for $RETRY_INTERVAL seconds (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

echo "Database $DB_NAME is ready!"

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

# Get the port from environment variable or use default
PORT="${PORT:-10000}"
echo "Starting application on port $PORT..."

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 4 --log-level info
