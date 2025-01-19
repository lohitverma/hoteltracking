#!/bin/bash

# Exit on error
set -e

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check requirements
echo "Checking requirements..."
if ! command_exists docker; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create required directories
echo "Creating required directories..."
mkdir -p certbot/conf
mkdir -p certbot/www

# Build and start services
echo "Building and starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Initialize database
echo "Initializing database..."
docker-compose exec web alembic upgrade head

# Initial SSL certificate
echo "Setting up SSL certificate..."
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@hoteltracker.com \
    --agree-tos \
    --no-eff-email \
    -d hoteltracker.com \
    -d www.hoteltracker.com

# Reload nginx to apply SSL configuration
echo "Reloading Nginx..."
docker-compose exec nginx nginx -s reload

echo "Deployment completed successfully!"
echo "Your application is now running at https://hoteltracker.com"
