# Quick Reference Guide

## DNS Records
```
A     @    → 76.76.21.21
CNAME api  → hotel-tracker-api.onrender.com
CNAME www  → hotel-tracker-api.onrender.com
```

## Essential URLs
```
Main:     https://hoteltracker.org
API:      https://api.hoteltracker.org
Docs:     https://api.hoteltracker.org/api/docs
Health:   https://api.hoteltracker.org/health
Metrics:  https://api.hoteltracker.org/metrics
```

## Key Configurations
```yaml
Port: 10000
Region: Ohio
SSL: Auto-provisioned
CORS: Enabled for all subdomains
HTTPS: Forced redirect
Health Check: Every 60s
```

## Common Tasks
1. **Add New Subdomain**
   - Add CNAME in Namecheap
   - Update ALLOWED_HOSTS
   - Update CORS origins
   - Update TrustedHostMiddleware

2. **SSL Renewal**
   - Automatic via Render
   - Check: ssllabs.com/ssltest/

3. **Monitoring**
   - Health: /health
   - Metrics: /metrics
   - Logs: Render dashboard
