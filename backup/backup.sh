#!/bin/bash

# Set timestamp for backup files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p /backup

# Set PostgreSQL password
export PGPASSWORD=postgres

# Backup PostgreSQL data
echo "Starting PostgreSQL backup..."
pg_dump -h db -U postgres -d hotel_tracker > /backup/postgres_${TIMESTAMP}.sql

# Keep only last 7 days of backups locally
echo "Cleaning up old backups..."
find /backup -name "postgres_*.sql" -type f -mtime +7 -delete

echo "Backup completed successfully"
