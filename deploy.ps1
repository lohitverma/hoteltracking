# Hotel Price Tracker Deployment Script
Write-Host "Starting Hotel Price Tracker Deployment..." -ForegroundColor Green

# 1. Environment Check
Write-Host "Checking environment..." -ForegroundColor Cyan
$requiredCommands = @("docker", "docker-compose", "git")
foreach ($cmd in $requiredCommands) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "Error: $cmd is not installed!" -ForegroundColor Red
        exit 1
    }
}

# 2. Environment Variables
Write-Host "Loading environment variables..." -ForegroundColor Cyan
if (!(Test-Path .env.production)) {
    Write-Host "Error: .env.production file not found!" -ForegroundColor Red
    exit 1
}

# 3. Backup Current State
Write-Host "Creating backup..." -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker-compose -f docker-compose.deploy.yml exec -T db pg_dump -U postgres hoteltracker > "backup_${timestamp}.sql"

# 4. Pull Latest Changes
Write-Host "Pulling latest changes..." -ForegroundColor Cyan
git pull origin main

# 5. Build Images
Write-Host "Building Docker images..." -ForegroundColor Cyan
docker-compose -f docker-compose.deploy.yml build --no-cache

# 6. Database Migrations
Write-Host "Running database migrations..." -ForegroundColor Cyan
docker-compose -f docker-compose.deploy.yml run --rm web alembic upgrade head

# 7. Start Services
Write-Host "Starting services..." -ForegroundColor Cyan
docker-compose -f docker-compose.deploy.yml up -d

# 8. Health Checks
Write-Host "Performing health checks..." -ForegroundColor Cyan
$healthCheckEndpoint = "http://localhost:8000/health"
$maxRetries = 10
$retryCount = 0
$healthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri $healthCheckEndpoint -Method Get
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    }
    catch {
        Write-Host "Health check attempt $($retryCount + 1) failed. Retrying..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        $retryCount++
    }
}

if ($healthy) {
    Write-Host "Deployment successful! Application is healthy." -ForegroundColor Green
    
    # Display service status
    Write-Host "`nService Status:" -ForegroundColor Cyan
    docker-compose -f docker-compose.deploy.yml ps
    
    Write-Host "`nAccess Points:" -ForegroundColor Cyan
    Write-Host "Main Application: http://localhost:8000"
    Write-Host "Monitoring Dashboard: http://localhost:3000"
    Write-Host "Prometheus Metrics: http://localhost:9090"
} else {
    Write-Host "Deployment failed! Application is not healthy." -ForegroundColor Red
    Write-Host "Rolling back to previous state..." -ForegroundColor Yellow
    
    # Rollback
    docker-compose -f docker-compose.deploy.yml down
    Get-Content "backup_${timestamp}.sql" | docker-compose -f docker-compose.deploy.yml exec -T db psql -U postgres hoteltracker
    docker-compose -f docker-compose.deploy.yml up -d
    
    Write-Host "Rollback complete. Please check the logs for errors." -ForegroundColor Yellow
    exit 1
}
