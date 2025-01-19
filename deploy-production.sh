#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Installing..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create required directories
echo "Creating required directories..."
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p backups

# Configure AWS credentials
echo "Configuring AWS credentials..."
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set default.region us-west-2

# Login to ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ECR_REGISTRY

# Pull latest images
echo "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Start services
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T web alembic upgrade head

# Initialize Grafana dashboards
echo "Setting up Grafana dashboards..."
curl -X POST -H "Content-Type: application/json" -d '{
    "name":"Hotel Tracker Dashboard",
    "type":"file",
    "url":"https://grafana.com/api/dashboards/12345/revisions/1/download"
}' http://admin:${GRAFANA_ADMIN_PASSWORD:-admin}@localhost:3000/api/dashboards/import

# Set up SSL certificate
echo "Setting up SSL certificate..."
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@hoteltracker.com \
    --agree-tos \
    --no-eff-email \
    -d hoteltracker.com \
    -d www.hoteltracker.com

# Reload nginx to apply SSL configuration
echo "Reloading Nginx..."
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Set up automatic backups
echo "Setting up automatic backups..."
aws s3 mb s3://${BACKUP_S3_BUCKET} || true
aws s3api put-bucket-lifecycle-configuration \
    --bucket ${BACKUP_S3_BUCKET} \
    --lifecycle-configuration '{
        "Rules": [{
            "ID": "RetentionRule",
            "Status": "Enabled",
            "ExpirationInDays": 30
        }]
    }'

# Clean up old images
echo "Cleaning up old images..."
docker system prune -f

echo "Deployment completed successfully!"
echo "Your application is now running at https://hoteltracker.com"
echo "Grafana dashboard is available at https://hoteltracker.com:3000"
echo "Prometheus metrics are available at https://hoteltracker.com:9090"
