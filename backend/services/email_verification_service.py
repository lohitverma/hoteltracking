from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
from jinja2 import Environment, FileSystemLoader

from models import User, EmailVerification
from database import get_db

logger = logging.getLogger(__name__)

class EmailVerificationService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_sender = os.getenv("EMAIL_SENDER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.verification_token_secret = os.getenv("VERIFICATION_TOKEN_SECRET")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Set up Jinja2 for email templates
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
    async def create_verification_token(self, user_id: int) -> str:
        """Create a verification token for email verification"""
        token_data = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "type": "email_verification"
        }
        
        return jwt.encode(
            token_data,
            self.verification_token_secret,
            algorithm="HS256"
        )
        
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a verification token"""
        try:
            payload = jwt.decode(
                token,
                self.verification_token_secret,
                algorithms=["HS256"]
            )
            
            if payload["type"] != "email_verification":
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link has expired"
            )
        except jwt.JWTError:
            return None
            
    async def send_verification_email(
        self,
        user: User,
        verification_token: str
    ) -> bool:
        """Send verification email to user"""
        try:
            # Create verification URL
            verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
            
            # Get email template
            template = self.jinja_env.get_template("verification_email.html")
            html_content = template.render(
                user_name=user.username,
                verification_url=verification_url
            )
            
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Verify your Hotel Tracker account"
            msg["From"] = self.email_sender
            msg["To"] = user.email
            
            # Add HTML content
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False
            
    async def create_verification_record(
        self,
        db: Session,
        user_id: int,
        token: str
    ) -> EmailVerification:
        """Create a verification record in the database"""
        verification = EmailVerification(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        return verification
        
    async def verify_email(
        self,
        db: Session,
        token: str
    ) -> Optional[User]:
        """Verify user's email address"""
        # Verify token
        payload = await self.verify_token(token)
        if not payload:
            return None
            
        user_id = payload["user_id"]
        
        # Get verification record
        verification = db.query(EmailVerification).filter(
            EmailVerification.user_id == user_id,
            EmailVerification.token == token,
            EmailVerification.used_at.is_(None),
            EmailVerification.expires_at > datetime.utcnow()
        ).first()
        
        if not verification:
            return None
            
        # Update user and verification record
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.email_verified = True
            verification.used_at = datetime.utcnow()
            db.commit()
            
        return user
        
    async def resend_verification_email(
        self,
        db: Session,
        user: User
    ) -> bool:
        """Resend verification email to user"""
        # Delete any existing unused verifications
        db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.used_at.is_(None)
        ).delete()
        
        # Create new verification token
        token = await self.create_verification_token(user.id)
        
        # Create verification record
        await self.create_verification_record(db, user.id, token)
        
        # Send email
        return await self.send_verification_email(user, token)
        
    async def check_verification_required(
        self,
        user: User
    ) -> bool:
        """Check if email verification is required for user"""
        # You can customize this based on your requirements
        return not user.email_verified
