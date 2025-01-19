#!/bin/bash

# Exit on error
set -e

# Load environment variables
source ../.env.production

# Set backup directory
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="hoteltracker_backup_${TIMESTAMP}"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
pg_dump -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -F c > ${BACKUP_DIR}/${BACKUP_NAME}.dump

# Backup application logs
echo "Backing up application logs..."
tar -czf ${BACKUP_DIR}/${BACKUP_NAME}_logs.tar.gz /var/log/hoteltracker/

# Upload to S3
echo "Uploading backups to S3..."
aws s3 cp ${BACKUP_DIR}/${BACKUP_NAME}.dump s3://${BACKUP_S3_BUCKET}/database/
aws s3 cp ${BACKUP_DIR}/${BACKUP_NAME}_logs.tar.gz s3://${BACKUP_S3_BUCKET}/logs/

# Clean up old backups (keep last 7 days)
echo "Cleaning up old backups..."
find ${BACKUP_DIR} -type f -mtime +7 -delete

echo "Backup completed successfully!"
