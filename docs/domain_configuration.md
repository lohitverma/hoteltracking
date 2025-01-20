# Domain Configuration Guide for hoteltracker.org

## 1. Domain Registration & DNS
### Namecheap Configuration
```plaintext
Domain: hoteltracker.org
Registrar: Namecheap
DNS Provider: Namecheap BasicDNS
```

### DNS Records
```plaintext
# Main Domain (Root/Apex)
Type: A Record
Host: @
Value: 76.76.21.21
TTL: Automatic

# API Subdomain
Type: CNAME Record
Host: api
Value: hotel-tracker-api.onrender.com
TTL: Automatic

# WWW Subdomain
Type: CNAME Record
Host: www
Value: hotel-tracker-api.onrender.com
TTL: Automatic
```

## 2. SSL/TLS Configuration
### Render.com SSL Settings
```yaml
# Auto-provisioned through Render.com
Certificate Type: Let's Encrypt
Auto-renewal: Enabled
Domains Covered:
  - hoteltracker.org
  - api.hoteltracker.org
  - www.hoteltracker.org
```

### Security Headers
```yaml
# HTTP Security Headers
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: 
  default-src: "'self'"
  img-src: ["'self'", "data:", "https:"]
  script-src: ["'self'", "'unsafe-inline'"]
  style-src: ["'self'", "'unsafe-inline'"]
```

## 3. Render.com Configuration
### Web Service Settings
```yaml
Name: hotel-tracker-api
Environment: Docker
Region: Ohio
Plan: Starter
Health Check Path: /health
Port: 10000

Environment Variables:
  PORT: 10000
  ENVIRONMENT: production
  DEBUG: false
  ALLOWED_HOSTS: .onrender.com,hoteltracker.org,api.hoteltracker.org,www.hoteltracker.org
  PYTHONUNBUFFERED: 1
  PYTHONDONTWRITEBYTECODE: 1
```

### Deployment Configuration
```yaml
Auto Deploy: Enabled
Branch: main
Build Command: docker build -t hotel-tracker .
Start Command: docker run -p 10000:10000 -e PORT=10000 hotel-tracker
```

## 4. Application Security
### HTTPS Configuration
```python
# FastAPI HTTPS Middleware
HTTPSRedirectMiddleware: Enabled
TrustedHostMiddleware:
  - hoteltracker.org
  - api.hoteltracker.org
  - www.hoteltracker.org
  - hotel-tracker-api.onrender.com
```

### CORS Policy
```python
origins = [
    "https://hoteltracker.org",
    "https://api.hoteltracker.org",
    "https://www.hoteltracker.org"
]
methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
headers = ["*"]
```

## 5. Monitoring Configuration
### Health Checks
```plaintext
Endpoint: /health
Method: GET
Frequency: 60 seconds
Timeout: 30 seconds
```

### Metrics
```plaintext
Endpoint: /metrics
Metrics Collected:
  - HTTP Request Count
  - Request Latency
  - Memory Usage
  - CPU Usage
```

## 6. Using This Configuration in a New Project

### 1. DNS Setup
1. Log in to Namecheap
2. Go to Domain List → Manage hoteltracker.org
3. Navigate to Advanced DNS
4. Add the A and CNAME records as specified above

### 2. Render.com Setup
1. Create new Web Service
2. Use the provided render.yaml as template
3. Update service name and environment variables
4. Configure domains in service settings

### 3. SSL Implementation
1. SSL certificates auto-provision on Render
2. Add security headers to your application
3. Implement HTTPS redirect
4. Configure CORS for your domains

### 4. Application Code
1. Update ALLOWED_HOSTS in your application
2. Implement security middleware
3. Add health check endpoint
4. Configure monitoring endpoints

### 5. Verification Steps
1. Check DNS propagation: `nslookup hoteltracker.org`
2. Verify SSL: https://www.ssllabs.com/ssltest/
3. Check security headers: https://securityheaders.com
4. Test health check endpoint
5. Monitor metrics endpoint

## 7. Important Notes
- Always backup DNS configurations before changes
- Keep SSL certificates auto-renewal enabled
- Regularly monitor security headers
- Keep CORS policies strict
- Maintain regular health checks
- Monitor SSL certificate expiration
- Keep security headers up to date

## 8. Useful Commands
```bash
# Check DNS
nslookup hoteltracker.org
nslookup api.hoteltracker.org
nslookup www.hoteltracker.org

# Test SSL
curl -vI https://hoteltracker.org
curl -vI https://api.hoteltracker.org
curl -vI https://www.hoteltracker.org

# Check HTTP to HTTPS redirect
curl -I http://hoteltracker.org
```
