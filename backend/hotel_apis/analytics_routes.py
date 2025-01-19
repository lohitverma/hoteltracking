from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/price-history/{hotel_id}")
async def get_price_history(
    hotel_id: int,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    """Get price history for a specific hotel"""
    analytics = AnalyticsService(db)
    return analytics.get_price_history(hotel_id, days)

@router.get("/price-trends/{hotel_id}")
async def get_price_trends(
    hotel_id: int,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    """Get price trends and forecast for a specific hotel"""
    analytics = AnalyticsService(db)
    return analytics.get_price_trends(hotel_id, days)

@router.get("/seasonal-analysis/{hotel_id}")
async def get_seasonal_analysis(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    """Get seasonal price patterns for a specific hotel"""
    analytics = AnalyticsService(db)
    return analytics.get_seasonal_analysis(hotel_id)

@router.get("/market-comparison/{hotel_id}")
async def get_market_comparison(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    """Compare hotel prices with others in the same location"""
    analytics = AnalyticsService(db)
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return analytics.get_market_comparison(hotel_id, hotel.location)
