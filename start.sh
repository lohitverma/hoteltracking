#!/bin/bash
set -e

echo "Starting application initialization..."

# Function to parse DATABASE_URL
parse_db_url() {
    # Try URLs in order: internal -> external -> fallback
    if [ -n "$INTERNAL_DATABASE_URL" ]; then
        DATABASE_URL="$INTERNAL_DATABASE_URL"
        echo "Using internal DATABASE_URL"
    elif [ -n "$EXTERNAL_DATABASE_URL" ]; then
        DATABASE_URL="$EXTERNAL_DATABASE_URL"
        echo "Using external DATABASE_URL"
    elif [ -z "$DATABASE_URL" ]; then
        echo "ERROR: No database URL configured"
        echo "Please set either INTERNAL_DATABASE_URL, EXTERNAL_DATABASE_URL, or DATABASE_URL"
        exit 1
    else
        echo "Using fallback DATABASE_URL"
    fi
    
    echo "Parsing DATABASE_URL..."
    
    # Extract components using pattern matching
    if [[ $DATABASE_URL =~ ^postgresql://([^:]+):([^@]+)@([^/]+)/(.+)$ ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASSWORD="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_NAME="${BASH_REMATCH[4]}"
        DB_PORT=5432
        
        export DB_USER DB_HOST DB_NAME DB_PORT DB_PASSWORD
        
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
    
    # Test PostgreSQL connection with SSL
    echo "Testing PostgreSQL connection with SSL..."
    if PGPASSWORD="$DB_PASSWORD" psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -c "SELECT version();" >/dev/null 2>&1; then
        echo "PostgreSQL SSL connection successful"
        return 0
    else
        echo "PostgreSQL SSL connection failed"
        return 1
    fi
}

# Function to check basic connectivity
check_postgres() {
    if PGPASSWORD="$DB_PASSWORD" psql "postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -c '\q' >/dev/null 2>&1; then
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

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Create alembic.ini if it doesn't exist
if [ ! -f "alembic.ini" ]; then
    echo "Creating alembic.ini..."
    cat > alembic.ini << EOL
[alembic]
script_location = migrations
sqlalchemy.url = ${DATABASE_URL}

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOL
fi

# Create migrations directory if it doesn't exist
if [ ! -d "migrations" ]; then
    echo "Creating migrations directory..."
    mkdir -p migrations
    
    # Create env.py
    echo "Creating migrations/env.py..."
    cat > migrations/env.py << 'EOL'
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from models import Base
target_metadata = Base.metadata

def get_url():
    if os.getenv("INTERNAL_DATABASE_URL"):
        return os.getenv("INTERNAL_DATABASE_URL")
    elif os.getenv("EXTERNAL_DATABASE_URL"):
        return os.getenv("EXTERNAL_DATABASE_URL")
    elif os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    else:
        raise ValueError("No database URL configured")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            'connect_timeout': 10,
            'application_name': 'hoteltracker_migrations',
            'sslmode': 'require'
        }
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOL

    # Create script.py.mako
    echo "Creating migrations/script.py.mako..."
    cat > migrations/script.py.mako << 'EOL'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
EOL
fi

# Create versions directory if it doesn't exist
echo "Ensuring migrations/versions directory exists..."
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
