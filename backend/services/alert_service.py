from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import PriceAlert, Hotel
from services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(
        self,
        db: Session,
        monitoring_service: MonitoringService
    ):
        self.db = db
        self.monitoring_service = monitoring_service
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_sender = os.getenv("EMAIL_SENDER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        # Start background task
        asyncio.create_task(self._check_alerts())
        
    async def create_alert(
        self,
        hotel_id: int,
        email: str,
        target_price: float
    ) -> Dict[str, Any]:
        """Create a new price alert"""
        try:
            # Check if hotel exists
            hotel = self.db.query(Hotel).filter(Hotel.id == hotel_id).first()
            if not hotel:
                raise ValueError("Hotel not found")
                
            # Create alert
            alert = PriceAlert(
                hotel_id=hotel_id,
                email=email,
                target_price=target_price
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            self.monitoring_service.track_price_alert("create", "active")
            
            return {
                "id": alert.id,
                "hotel_id": alert.hotel_id,
                "email": alert.email,
                "target_price": alert.target_price,
                "is_active": alert.is_active,
                "created_at": alert.created_at.isoformat()
            }
            
        except Exception as e:
            self.monitoring_service.track_price_alert("create", "failed")
            logger.error(f"Error creating alert: {str(e)}")
            raise
            
    async def delete_alert(self, alert_id: int) -> bool:
        """Delete a price alert"""
        alert = self.db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
        if not alert:
            return False
            
        alert.is_active = False
        self.db.commit()
        
        self.monitoring_service.track_price_alert("delete", "success")
        return True
        
    async def get_alerts(self, email: str) -> List[Dict[str, Any]]:
        """Get all active alerts for an email"""
        alerts = self.db.query(PriceAlert).filter(
            and_(
                PriceAlert.email == email,
                PriceAlert.is_active == True
            )
        ).all()
        
        return [
            {
                "id": alert.id,
                "hotel_id": alert.hotel_id,
                "target_price": alert.target_price,
                "created_at": alert.created_at.isoformat(),
                "last_checked": alert.last_checked.isoformat() if alert.last_checked else None,
                "last_notified": alert.last_notified.isoformat() if alert.last_notified else None
            }
            for alert in alerts
        ]
        
    async def _check_alerts(self):
        """Background task to check price alerts"""
        while True:
            try:
                alerts = self.db.query(PriceAlert).filter(
                    PriceAlert.is_active == True
                ).all()
                
                for alert in alerts:
                    await self._check_alert(alert)
                    
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error checking alerts: {str(e)}")
                await asyncio.sleep(60)
                
    async def _check_alert(self, alert: PriceAlert):
        """Check if price alert should be triggered"""
        try:
            hotel = self.db.query(Hotel).filter(Hotel.id == alert.hotel_id).first()
            if not hotel:
                return
                
            alert.last_checked = datetime.utcnow()
            
            if hotel.current_price <= alert.target_price:
                # Price target reached
                if not alert.last_notified or \
                   datetime.utcnow() - alert.last_notified > timedelta(days=1):
                    # Send notification if not sent in last 24 hours
                    await self._send_alert_email(alert, hotel)
                    alert.last_notified = datetime.utcnow()
                    self.monitoring_service.track_price_alert("notify", "sent")
                    
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {str(e)}")
            self.monitoring_service.track_price_alert("notify", "failed")
            
    async def _send_alert_email(self, alert: PriceAlert, hotel: Hotel):
        """Send price alert email"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Price Alert: {hotel.name} price dropped!"
            msg["From"] = self.email_sender
            msg["To"] = alert.email
            
            html = f"""
            <html>
                <body>
                    <h2>Price Alert Triggered!</h2>
                    <p>Good news! The price for {hotel.name} has dropped to ${hotel.current_price:.2f},
                    which is below your target price of ${alert.target_price:.2f}.</p>
                    
                    <h3>Hotel Details:</h3>
                    <ul>
                        <li>Name: {hotel.name}</li>
                        <li>City: {hotel.city}</li>
                        <li>Current Price: ${hotel.current_price:.2f}</li>
                        <li>Your Target: ${alert.target_price:.2f}</li>
                        <li>Rating: {hotel.rating}/5</li>
                    </ul>
                    
                    <p>Book now to secure this rate!</p>
                    
                    <p>Best regards,<br>Hotel Price Tracker</p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Error sending alert email: {str(e)}")
            raise
