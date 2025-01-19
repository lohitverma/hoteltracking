# Create directories for certbot
New-Item -ItemType Directory -Force -Path "certbot/conf"
New-Item -ItemType Directory -Force -Path "certbot/www"

# Stop any running containers
docker-compose -f docker-compose.deploy.yml down

# Start nginx
docker-compose -f docker-compose.deploy.yml up -d nginx

# Get SSL certificate
docker-compose -f docker-compose.deploy.yml run --rm certbot certonly `
    --webroot `
    --webroot-path=/var/www/certbot `
    --email admin@hoteltracker.org `
    --agree-tos `
    --no-eff-email `
    -d hoteltracker.org `
    -d www.hoteltracker.org

# Restart nginx to load the certificates
docker-compose -f docker-compose.deploy.yml restart nginx

# Start all other services
docker-compose -f docker-compose.deploy.yml up -d
