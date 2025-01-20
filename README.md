# 🏨 Hotel Price Tracker

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A professional hotel price tracking platform with real-time alerts and analytics.

## ✨ Features

- 🔍 Real-time hotel price tracking
- 📊 Advanced analytics and insights
- 🔔 SMS and email price alerts
- 📍 User authentication and preferences
- 📈 Price history visualization
- 📱 Mobile-responsive design
- 🚀 High-performance async operations
- 🔒 Rate limiting and security features

## 🚀 Setup Instructions

### Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL database

4. Create .env file:
   ```bash
   cp backend/.env.example backend/.env
   # Update the .env file with your credentials
   ```

5. Initialize the database:
   ```bash
   alembic upgrade head
   ```

6. Run the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

### Production Deployment

1. Domain Setup:
   - Purchase domain (e.g., hoteltracker.com)
   - Set up DNS records
   - Configure SSL certificates

2. Server Setup:
   - Deploy on cloud provider (AWS/GCP/Azure)
   - Set up Nginx as reverse proxy
   - Configure PostgreSQL database
   - Set up Redis for caching

3. CI/CD Pipeline:
   - GitHub Actions for automated testing
   - Automated deployment to staging/production

### Third-Party Services Setup

1. Twilio (SMS Alerts):
   - Sign up for Twilio account
   - Get Account SID and Auth Token
   - Add verified phone number

2. SendGrid (Email Notifications):
   - Create SendGrid account
   - Generate API key
   - Verify sender email

3. Segment (Analytics):
   - Create Segment account
   - Get Write Key
   - Set up tracking plan

## 🔧 Environment Variables

Create a `.env` file with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost/hoteltracker
SECRET_KEY=your-secret-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=your-verified-email
SEGMENT_WRITE_KEY=your-segment-key
```

## 📈 API Documentation

Access the API documentation at `/docs` endpoint.

## 🔒 Security Features

- Rate Limiting
- JWT Authentication
- CORS Protection
- Input Validation
- SQL Injection Prevention
- XSS Protection

## 📚 Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

## 📝 License

MIT License

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- Render for hosting
- All our contributors and users

## Hotel Price Tracking API

A comprehensive API for tracking hotel prices and managing alerts.

### Features

- Real-time hotel price tracking
- Price alerts and notifications
- User authentication with OAuth2
- API key management
- Rate limiting
- Redis-based caching
- OpenAPI documentation

### Getting Started

#### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Node.js 14+

#### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hotel-tracker.git
cd hotel-tracker
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/hotel_tracker

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback/google

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/callback/github

# Notifications
EMAIL_SENDER=your-email@example.com
EMAIL_PASSWORD=your-email-password
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
```

4. Initialize the database:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn main:app --reload
```

### API Documentation

#### Authentication

The API supports three authentication methods:

1. OAuth2 (Google and GitHub)
2. API Keys
3. JWT Tokens

#### OAuth2 Endpoints

- `GET /auth/login/google`: Get Google OAuth login URL
- `GET /auth/login/github`: Get GitHub OAuth login URL
- `GET /auth/callback/google`: Handle Google callback
- `GET /auth/callback/github`: Handle GitHub callback

#### JWT Authentication

- `POST /auth/register`: Register new user
- `POST /auth/login`: Login and get tokens
- `POST /auth/refresh`: Refresh access token
- `GET /auth/me`: Get current user info
- `POST /auth/logout`: Logout user

#### API Keys

- `POST /api/keys`: Create new API key
- `GET /api/keys`: List user's API keys
- `DELETE /api/keys/{key_id}`: Revoke API key
- `GET /api/keys/scopes`: List available scopes

### Hotel Endpoints

- `GET /api/hotels/search`: Search hotels (cached)
  - Parameters:
    - `query`: Search query
    - `location`: City name
    - `check_in`: Check-in date
    - `check_out`: Check-out date
    - `guests`: Number of guests (default: 2)

- `GET /api/hotels/{hotel_id}/prices`: Get price history (cached)
  - Parameters:
    - `start_date`: Start date
    - `end_date`: End date

### Alert Endpoints

- `POST /api/alerts`: Create price alert
- `GET /api/alerts/notifications`: Get user notifications
- `POST /api/alerts/check`: Trigger alert checks

### Cache Management

- `GET /api/cache/stats`: Get cache statistics
- `POST /api/cache/clear/{pattern}`: Clear cache by pattern

### Rate Limiting

The API implements rate limiting:

- General endpoints: 60 requests per minute
- Search endpoints: 30 requests per minute
- API key creation: 5 requests per hour

Rate limit headers are included in responses:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

### Monitoring

- `GET /metrics`: Prometheus metrics
- `GET /health`: Application health status

### Interactive Documentation

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Development

#### Running Tests

```bash
pytest
```

#### Code Style

```bash
# Format code
black .

# Check types
mypy .

# Lint code
flake8
```

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
