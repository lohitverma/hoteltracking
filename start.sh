#!/bin/bash
set -e

echo "Starting application initialization..."

# Function to get database connection parameters from DATABASE_URL or individual vars
get_db_params() {
    local url=""
    
    # Check for internal connection with key
    if [ ! -z "$RENDER_INTERNAL_DATABASE_URL" ] && [ ! -z "$RENDER_INTERNAL_DB_KEY" ]; then
        url="$RENDER_INTERNAL_DATABASE_URL"
        echo "Using RENDER_INTERNAL_DATABASE_URL with internal key"
    # Check for external connection with key
    elif [ ! -z "$DATABASE_URL" ] && [ ! -z "$RENDER_EXTERNAL_DB_KEY" ]; then
        url="$DATABASE_URL"
        echo "Using DATABASE_URL with external key"
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
echo "Internal Key Present: $([ ! -z "$RENDER_INTERNAL_DB_KEY" ] && echo "Yes" || echo "No")"
echo "External Key Present: $([ ! -z "$RENDER_EXTERNAL_DB_KEY" ] && echo "Yes" || echo "No")"

# Function to check if we can connect to PostgreSQL server
check_postgres() {
    # Try basic connection
    if PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c '\q' "sslmode=require" 2>/dev/null; then
        echo "Basic connection successful"
        return 0
    fi
    return 1
}

# Function to check database exists
database_exists() {
    if PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' "sslmode=require" 2>/dev/null; then
        echo "Database exists and is accessible"
        return 0
    fi
    return 1
}

# Function to run detailed database checks
check_database_details() {
    echo "Running detailed database checks..."
    
    # Check SSL
    echo "Checking SSL connection..."
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SHOW ssl;" "sslmode=require" || echo "SSL check failed"
    
    # Check version
    echo "Checking PostgreSQL version..."
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SHOW server_version;" "sslmode=require" || echo "Version check failed"
    
    # Check user permissions
    echo "Checking user permissions..."
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT current_user, current_database();" "sslmode=require" || echo "Permission check failed"
}

# Wait for PostgreSQL server to be ready
MAX_RETRIES=60
RETRY_INTERVAL=5
RETRY_COUNT=0

echo "Testing network connectivity..."
if command -v nc &> /dev/null; then
    echo "Testing with nc..."
    nc -zv "$DB_HOST" "$DB_PORT" 2>&1 || echo "nc command failed"
fi

if command -v ping &> /dev/null; then
    echo "Testing with ping..."
    ping -c 1 "$DB_HOST" || echo "ping command failed"
fi

if command -v dig &> /dev/null; then
    echo "Testing with dig..."
    dig "$DB_HOST" || echo "dig command failed"
fi

if command -v nslookup &> /dev/null; then
    echo "Testing with nslookup..."
    nslookup "$DB_HOST" || echo "nslookup command failed"
fi

echo "Testing TCP connection..."
timeout 5 bash -c "</dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null && echo "TCP connection successful" || echo "TCP connection failed"

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

# Run detailed database checks
check_database_details

# Create database if it doesn't exist
if ! database_exists; then
    echo "Database $DB_NAME does not exist. Creating..."
    PGPASSWORD=$DB_PASSWORD createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" || {
        echo "Failed to create database"
        exit 1
    }
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
