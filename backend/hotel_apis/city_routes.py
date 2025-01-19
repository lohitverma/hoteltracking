from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from services.location_service import LocationService
from services.aggregator import HotelAggregator
from models import Hotel, User, PriceAlert
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cities", tags=["cities"])

@router.get("/search")
async def search_cities(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """Search for cities by name"""
    location_service = LocationService()
    try:
        cities = await location_service.search_cities(query)
        return cities
    finally:
        await location_service.close()

@router.get("/popular")
async def get_popular_cities(db: Session = Depends(get_db)):
    """Get list of popular cities"""
    location_service = LocationService()
    try:
        return await location_service.get_popular_destinations()
    finally:
        await location_service.close()

@router.get("/{city_id}")
async def get_city_details(
    city_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific city"""
    location_service = LocationService()
    try:
        city = await location_service.get_city_details(city_id)
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        return city
    finally:
        await location_service.close()

@router.get("/{city_id}/hotels")
async def get_city_hotels(
    city_id: str,
    radius: Optional[int] = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get hotels in a specific city"""
    location_service = LocationService()
    try:
        hotels = await location_service.get_city_hotels(city_id, radius)
        if not hotels:
            raise HTTPException(status_code=404, detail="No hotels found in this city")
        return hotels
    finally:
        await location_service.close()

@router.get("/{city_id}/stats")
async def get_city_stats(
    city_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics about hotels in a city"""
    location_service = LocationService()
    try:
        stats = await location_service.get_city_stats(city_id)
        return stats
    finally:
        await location_service.close()

@router.post("/{city_id}/track")
async def track_city_hotels(
    city_id: str,
    radius: Optional[int] = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Start tracking all hotels in a city"""
    location_service = LocationService()
    aggregator = HotelAggregator(db)
    
    try:
        # Get all hotels in the city
        hotels = await location_service.get_city_hotels(city_id, radius)
        if not hotels:
            raise HTTPException(status_code=404, detail="No hotels found in this city")
            
        tracked_hotels = []
        for hotel_data in hotels:
            # Check if hotel already exists in database
            hotel = db.query(Hotel).filter(Hotel.hotel_id == hotel_data['hotel_id']).first()
            
            if not hotel:
                # Add new hotel to database
                hotel = Hotel(
                    hotel_id=hotel_data['hotel_id'],
                    name=hotel_data['name'],
                    location=hotel_data['city_name'],
                    rating=hotel_data['rating']
                )
                db.add(hotel)
                db.commit()
                
            # Start tracking price for this hotel
            await aggregator.track_price_changes(hotel.hotel_id)
            tracked_hotels.append(hotel_data)
            
        return {
            "message": f"Started tracking {len(tracked_hotels)} hotels in {hotels[0]['city_name']}",
            "tracked_hotels": tracked_hotels
        }
        
    except Exception as e:
        logger.error(f"Error tracking city hotels: {str(e)}")
        raise HTTPException(status_code=500, detail="Error tracking city hotels")
    finally:
        await location_service.close()
