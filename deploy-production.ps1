# Load environment variables
$envContent = Get-Content .env
foreach ($line in $envContent) {
    if ($line -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        [Environment]::SetEnvironmentVariable($name, $value)
    }
}

# Check if Docker is installed
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed. Please install Docker Desktop for Windows."
    exit 1
}

# Check if AWS CLI is installed
if (-not (Get-Command "aws" -ErrorAction SilentlyContinue)) {
    Write-Host "AWS CLI is not installed. Installing..."
    Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
    Start-Process msiexec.exe -Wait -ArgumentList "/i AWSCLIV2.msi /quiet"
    Remove-Item "AWSCLIV2.msi"
}

# Create required directories
Write-Host "Creating required directories..."
New-Item -ItemType Directory -Force -Path "certbot/conf"
New-Item -ItemType Directory -Force -Path "certbot/www"
New-Item -ItemType Directory -Force -Path "backups"

# Configure AWS credentials
Write-Host "Configuring AWS credentials..."
aws configure set aws_access_key_id $env:AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $env:AWS_SECRET_ACCESS_KEY
aws configure set default.region us-west-2

# Login to ECR
Write-Host "Logging in to Amazon ECR..."
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $env:ECR_REGISTRY

# Pull latest images
Write-Host "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Start services
Write-Host "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
Write-Host "Waiting for services to be ready..."
Start-Sleep -Seconds 30

# Run database migrations
Write-Host "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T web alembic upgrade head

# Initialize Grafana dashboards
Write-Host "Setting up Grafana dashboards..."
$grafanaPassword = if ($env:GRAFANA_ADMIN_PASSWORD) { $env:GRAFANA_ADMIN_PASSWORD } else { "admin" }
$dashboardJson = @{
    name = "Hotel Tracker Dashboard"
    type = "file"
    url = "https://grafana.com/api/dashboards/12345/revisions/1/download"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
    -Uri "http://localhost:3000/api/dashboards/import" `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:$grafanaPassword"))
    } `
    -Body $dashboardJson

# Set up SSL certificate
Write-Host "Setting up SSL certificate..."
docker-compose -f docker-compose.prod.yml run --rm certbot certonly `
    --webroot `
    --webroot-path=/var/www/certbot `
    --email admin@hoteltracker.com `
    --agree-tos `
    --no-eff-email `
    -d hoteltracker.com `
    -d www.hoteltracker.com

# Reload nginx to apply SSL configuration
Write-Host "Reloading Nginx..."
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Set up automatic backups
Write-Host "Setting up automatic backups..."
aws s3 mb "s3://$env:BACKUP_S3_BUCKET" --force
$lifecycleConfig = @{
    Rules = @(
        @{
            ID = "RetentionRule"
            Status = "Enabled"
            ExpirationInDays = 30
        }
    )
} | ConvertTo-Json -Depth 10

aws s3api put-bucket-lifecycle-configuration `
    --bucket $env:BACKUP_S3_BUCKET `
    --lifecycle-configuration $lifecycleConfig

# Clean up old images
Write-Host "Cleaning up old images..."
docker system prune -f

Write-Host "Deployment completed successfully!"
Write-Host "Your application is now running at https://hoteltracker.com"
Write-Host "Grafana dashboard is available at https://hoteltracker.com:3000"
Write-Host "Prometheus metrics are available at https://hoteltracker.com:9090"
