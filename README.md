# Hotel Price Tracker

A professional hotel price tracking platform with real-time alerts and analytics.

## Features

- Real-time hotel price tracking
- SMS and email price alerts
- Advanced analytics and insights
- User authentication and preferences
- Price history visualization
- Search history tracking
- Mobile-responsive design

## Tech Stack

### Backend
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy ORM
- Twilio (SMS alerts)
- SendGrid (Email notifications)
- Segment (Analytics)
- JWT Authentication

### Frontend
- React
- Chart.js
- Tailwind CSS
- Socket.IO (Real-time updates)

## Setup Instructions

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

## Environment Variables

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

## API Documentation

Access the API documentation at `/docs` endpoint.

## Analytics Dashboard

Access analytics at `/analytics` endpoint (admin only).

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

## License

MIT License
