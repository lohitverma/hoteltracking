#!/bin/bash

# Exit on error
set -e

# Load environment variables
source ../.env.production

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Please provide the backup timestamp (YYYYMMDD_HHMMSS)"
    exit 1
fi

TIMESTAMP=$1
BACKUP_NAME="hoteltracker_backup_${TIMESTAMP}"
BACKUP_DIR="/backups"

# Download from S3
echo "Downloading backup from S3..."
aws s3 cp s3://${BACKUP_S3_BUCKET}/database/${BACKUP_NAME}.dump ${BACKUP_DIR}/
aws s3 cp s3://${BACKUP_S3_BUCKET}/logs/${BACKUP_NAME}_logs.tar.gz ${BACKUP_DIR}/

# Restore PostgreSQL database
echo "Restoring PostgreSQL database..."
pg_restore -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c ${BACKUP_DIR}/${BACKUP_NAME}.dump

# Restore logs
echo "Restoring logs..."
tar -xzf ${BACKUP_DIR}/${BACKUP_NAME}_logs.tar.gz -C /

echo "Restore completed successfully!"
