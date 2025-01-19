import os
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from services.aggregator import HotelAggregator
from database import SessionLocal
from models import Hotel, PriceAlert, User
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery('hotel_tracker',
                broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
                backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@celery.task
def update_hotel_prices():
    """Update prices for all tracked hotels"""
    db = SessionLocal()
    try:
        aggregator = HotelAggregator(db)
        hotels = db.query(Hotel).all()
        
        for hotel in hotels:
            try:
                # Run price tracking in event loop
                loop = asyncio.get_event_loop()
                loop.run_until_complete(aggregator.track_price_changes(hotel.hotel_id))
            except Exception as e:
                logger.error(f"Error updating price for hotel {hotel.hotel_id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in price update task: {str(e)}")
    finally:
        db.close()

@celery.task
def check_price_alerts():
    """Check price alerts and notify users"""
    db = SessionLocal()
    try:
        alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).all()
        aggregator = HotelAggregator(db)
        
        for alert in alerts:
            try:
                # Get current best price
                loop = asyncio.get_event_loop()
                best_price = loop.run_until_complete(
                    aggregator.get_best_price(
                        hotel_id=alert.hotel.hotel_id,
                        check_in=datetime.now(),
                        check_out=datetime.now() + timedelta(days=1),
                        guests=2
                    )
                )
                
                if best_price and best_price.price <= alert.target_price:
                    # Send notification
                    from services import NotificationService
                    notification_service = NotificationService()
                    
                    message = (
                        f"Price Alert! {alert.hotel.name} is now available at "
                        f"${best_price.price} on {best_price.provider}\n"
                        f"Book now: {best_price.url}"
                    )
                    
                    if alert.alert_type in ['sms', 'both']:
                        notification_service.send_sms_alert(
                            alert.user.phone_number,
                            message
                        )
                        
                    if alert.alert_type in ['email', 'both']:
                        notification_service.send_email_alert(
                            alert.user.email,
                            "Hotel Price Alert",
                            message
                        )
                        
                    # Update alert status
                    alert.is_active = False
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Error processing alert {alert.id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in alert check task: {str(e)}")
    finally:
        db.close()

# Schedule tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Update prices every hour
    sender.add_periodic_task(
        3600.0,
        update_hotel_prices.s(),
        name='update-hotel-prices'
    )
    
    # Check alerts every 15 minutes
    sender.add_periodic_task(
        900.0,
        check_price_alerts.s(),
        name='check-price-alerts'
    )
