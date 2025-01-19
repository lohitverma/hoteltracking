from typing import List, Optional
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel
from jinja2 import Environment, select_autoescape, PackageLoader

class EmailNotificationService:
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_FROM=os.getenv("MAIL_FROM", "notifications@hoteltracker.com"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
            MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True
        )
        self.fastmail = FastMail(self.config)
        self.jinja_env = Environment(
            loader=PackageLoader("backend", "templates/email"),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_price_alert(
        self,
        email: EmailStr,
        hotel_name: str,
        current_price: float,
        previous_price: float,
        currency: str = "USD"
    ):
        """Send price alert email when hotel price changes significantly."""
        template = self.jinja_env.get_template("price_alert.html")
        price_change = ((current_price - previous_price) / previous_price) * 100
        
        html = template.render(
            hotel_name=hotel_name,
            current_price=f"{current_price:.2f}",
            previous_price=f"{previous_price:.2f}",
            price_change=f"{price_change:.1f}",
            currency=currency
        )

        message = MessageSchema(
            subject=f"Price Alert: {hotel_name} price has changed!",
            recipients=[email],
            body=html,
            subtype="html"
        )

        await self.fastmail.send_message(message)

    async def send_booking_confirmation(
        self,
        email: EmailStr,
        booking_details: dict,
        itinerary_pdf: Optional[bytes] = None
    ):
        """Send booking confirmation email with optional PDF itinerary."""
        template = self.jinja_env.get_template("booking_confirmation.html")
        
        html = template.render(
            booking_id=booking_details["booking_id"],
            hotel_name=booking_details["hotel_name"],
            check_in=booking_details["check_in"],
            check_out=booking_details["check_out"],
            total_price=booking_details["total_price"],
            currency=booking_details.get("currency", "USD")
        )

        message = MessageSchema(
            subject=f"Booking Confirmation - {booking_details['hotel_name']}",
            recipients=[email],
            body=html,
            subtype="html"
        )

        if itinerary_pdf:
            message.attachments = [
                {
                    "file": itinerary_pdf,
                    "filename": f"itinerary_{booking_details['booking_id']}.pdf",
                    "headers": {"Content-Type": "application/pdf"}
                }
            ]

        await self.fastmail.send_message(message)

    async def send_travel_tips(
        self,
        email: EmailStr,
        destination: str,
        travel_dates: tuple[str, str],
        preferences: List[str]
    ):
        """Send personalized travel tips based on destination and preferences."""
        template = self.jinja_env.get_template("travel_tips.html")
        
        html = template.render(
            destination=destination,
            arrival_date=travel_dates[0],
            departure_date=travel_dates[1],
            preferences=preferences
        )

        message = MessageSchema(
            subject=f"Your Personalized Travel Guide for {destination}",
            recipients=[email],
            body=html,
            subtype="html"
        )

        await self.fastmail.send_message(message)

    async def send_price_prediction(
        self,
        email: EmailStr,
        hotel_name: str,
        current_price: float,
        predicted_prices: List[dict],
        currency: str = "USD"
    ):
        """Send price prediction email with trend analysis."""
        template = self.jinja_env.get_template("price_prediction.html")
        
        html = template.render(
            hotel_name=hotel_name,
            current_price=f"{current_price:.2f}",
            predicted_prices=predicted_prices,
            currency=currency
        )

        message = MessageSchema(
            subject=f"Price Prediction Report - {hotel_name}",
            recipients=[email],
            body=html,
            subtype="html"
        )

        await self.fastmail.send_message(message)

# Global notification service instance
notification_service = EmailNotificationService()
