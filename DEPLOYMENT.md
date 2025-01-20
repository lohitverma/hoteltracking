# Hotel Tracker Production Deployment Guide

## Pre-deployment Checklist

### 1. Environment Configuration
- [ ] Update `.env.production` with secure credentials
- [ ] Configure SSL certificates
- [ ] Set up domain names and DNS records
- [ ] Configure email service
- [ ] Set up monitoring services

### 2. Security Checks
- [ ] Run security audit: `npm audit` (frontend) and `safety check` (backend)
- [ ] Update dependencies to latest secure versions
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Configure proper authentication

### 3. Performance Optimization
- [ ] Run performance audit
- [ ] Optimize images and assets
- [ ] Enable compression
- [ ] Configure caching
- [ ] Set up CDN
- [ ] Optimize database queries
- [ ] Configure Redis caching

### 4. Testing
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Run end-to-end tests
- [ ] Test all critical user flows
- [ ] Load test the application
- [ ] Test backup and restore procedures

### 5. Monitoring Setup
- [ ] Configure error tracking (Sentry)
- [ ] Set up performance monitoring
- [ ] Configure logging
- [ ] Set up alerts
- [ ] Test monitoring systems

## Deployment Steps

1. **Prepare Infrastructure**
   ```bash
   # Create necessary directories
   mkdir -p nginx/ssl nginx/conf.d nginx/www
   
   # Generate SSL certificates
   certbot certonly --webroot -w /var/www/certbot -d hoteltracker.com -d www.hoteltracker.com
   ```

2. **Build and Push Docker Images**
   ```bash
   # Build images
   docker-compose -f docker-compose.yml build

   # Push to registry
   docker-compose -f docker-compose.yml push
   ```

3. **Database Migration**
   ```bash
   # Run database migrations
   docker-compose exec backend alembic upgrade head

   # Verify database state
   docker-compose exec backend alembic current
   ```

4. **Deploy Application**
   ```bash
   # Pull latest images
   docker-compose pull

   # Start services
   docker-compose up -d

   # Verify deployment
   docker-compose ps
   ```

5. **Post-deployment Verification**
   ```bash
   # Check logs
   docker-compose logs -f

   # Monitor services
   docker stats

   # Test endpoints
   curl -k https://hoteltracker.com/health
   ```

## Rollback Procedure

If issues are detected, follow these steps to rollback:

1. **Revert to Previous Version**
   ```bash
   # Stop current version
   docker-compose down

   # Pull previous version
   docker-compose pull previous-tag

   # Start previous version
   docker-compose up -d
   ```

2. **Database Rollback**
   ```bash
   # Rollback last migration
   docker-compose exec backend alembic downgrade -1
   ```

## Monitoring and Maintenance

### Daily Checks
- [ ] Review error logs
- [ ] Check system metrics
- [ ] Monitor database performance
- [ ] Review security alerts
- [ ] Check backup status

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Analyze user feedback
- [ ] Review and update documentation
- [ ] Test disaster recovery procedures

### Monthly Tasks
- [ ] Full security audit
- [ ] Update SSL certificates if needed
- [ ] Review and optimize costs
- [ ] Clean up unused resources
- [ ] Test scaling procedures

## Emergency Contacts

- **DevOps Team**: devops@hoteltracker.com
- **Security Team**: security@hoteltracker.com
- **Database Admin**: dba@hoteltracker.com
- **System Admin**: sysadmin@hoteltracker.com

## Additional Resources

- [Monitoring Dashboard](https://grafana.hoteltracker.com)
- [Error Tracking](https://sentry.hoteltracker.com)
- [API Documentation](https://api.hoteltracker.com/docs)
- [Internal Wiki](https://wiki.hoteltracker.com)
