# Namecheap DNS Configuration Guide for Hotel Tracker

## DNS Records Setup

### 1. Root Domain (hoteltracker.com)
```
Type: A
Host: @
Value: [Your Render.com IP]
TTL: Automatic
```

### 2. WWW Subdomain
```
Type: CNAME
Host: www
Value: [Your Render.com URL]
TTL: Automatic
```

### 3. API Subdomain
```
Type: CNAME
Host: api
Value: [Your Render.com Backend URL]
TTL: Automatic
```

## Steps to Configure

1. **Login to Namecheap**
   - Go to [Namecheap.com](https://www.namecheap.com)
   - Login to your account
   - Go to "Domain List"
   - Click "Manage" next to your domain

2. **Access Advanced DNS**
   - Click on "Advanced DNS" tab
   - Look for "Host Records" section

3. **Add/Edit Records**
   - Click "Add New Record" for each required record
   - Fill in the values as specified above
   - Save changes

4. **Configure URL Redirect Record**
   - Type: URL Redirect
   - Host: @
   - Value: https://www.hoteltracker.com
   - Redirect Type: Permanent (301)

5. **SSL/TLS Configuration**
   - Enable HTTPS redirect
   - Use Render.com's SSL certificate

## Verification Steps

1. **Check DNS Propagation**
   ```bash
   dig hoteltracker.com
   dig www.hoteltracker.com
   dig api.hoteltracker.com
   ```

2. **Verify SSL**
   ```bash
   curl -I https://hoteltracker.com
   curl -I https://www.hoteltracker.com
   curl -I https://api.hoteltracker.com
   ```

3. **Test Redirects**
   - http://hoteltracker.com → https://www.hoteltracker.com
   - http://www.hoteltracker.com → https://www.hoteltracker.com

## Common Issues

### DNS Propagation
- DNS changes can take up to 48 hours to propagate
- Use [whatsmydns.net](https://www.whatsmydns.net) to check propagation

### SSL Certificate Issues
- Ensure Render.com SSL is properly configured
- Check SSL certificate validity using browser tools

### Redirect Loops
- Verify redirect settings in both Namecheap and Render.com
- Test with curl -L to follow redirects

## Maintenance

### Regular Checks
- Monitor SSL certificate expiration
- Verify DNS records monthly
- Test all subdomains regularly

### Security Best Practices
- Enable DNSSEC if available
- Use strong TTL values
- Monitor for unauthorized DNS changes

## Support Contacts

- Namecheap Support: support@namecheap.com
- Render.com Support: support@render.com
- Internal DevOps: devops@hoteltracker.com
