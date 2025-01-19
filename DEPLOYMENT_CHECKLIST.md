# Hotel Price Tracker Deployment Checklist

## Pre-Deployment Checks
- [ ] All tests are passing (`pytest`)
- [ ] Code quality checks passed (black, flake8)
- [ ] Security scans completed (Snyk, Bandit)
- [ ] Database migrations are ready
- [ ] Environment variables are configured
- [ ] SSL certificates are valid
- [ ] Backup system is operational
- [ ] Monitoring systems are configured

## Required Environment Variables
```
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/hoteltracker

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_URL=redis://redis-cache:6379/1

# AWS (for backups)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=your_region
BACKUP_S3_BUCKET=your_bucket_name

# Security
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,hoteltracker.org
CORS_ORIGINS=http://localhost:3000,https://hoteltracker.org

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp
GRAFANA_ADMIN_PASSWORD=your_admin_password
```

## Deployment Steps
1. Run pre-deployment checks
   ```powershell
   .\scripts\pre-deploy-check.ps1
   ```

2. Create backup
   ```powershell
   .\scripts\backup.ps1
   ```

3. Deploy application
   ```powershell
   .\deploy.ps1
   ```

4. Verify deployment
   - [ ] Application is accessible
   - [ ] Database migrations completed
   - [ ] Monitoring systems are reporting
   - [ ] Backup system is operational
   - [ ] SSL certificates are active

## Post-Deployment Verification
- [ ] Health check endpoint returns 200
- [ ] API endpoints are responsive
- [ ] Database connections are stable
- [ ] Cache system is operational
- [ ] Logs are being collected
- [ ] Metrics are being recorded
- [ ] Alerts are properly configured

## Rollback Procedure
If deployment fails:
1. Stop services
   ```powershell
   docker-compose -f docker-compose.deploy.yml down
   ```

2. Restore backup
   ```powershell
   .\scripts\restore.ps1 [BACKUP_TIMESTAMP]
   ```

3. Start previous version
   ```powershell
   docker-compose -f docker-compose.deploy.yml up -d
   ```

## Monitoring URLs
- Application: https://hoteltracker.org
- Grafana: https://grafana.hoteltracker.org
- Prometheus: https://prometheus.hoteltracker.org
- Health Check: https://hoteltracker.org/health

## Support Contacts
- DevOps Team: devops@hoteltracker.org
- Backend Team: backend@hoteltracker.org
- Infrastructure: infra@hoteltracker.org
