from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import os
from dotenv import load_dotenv
from services.aggregator import HotelAggregator
from services.location_service import LocationService
from database import get_db
from sqlalchemy.orm import Session
from models import User, Hotel, PriceAlert
import logging
from hotel_apis.analytics_routes import router as analytics_router
from hotel_apis.city_routes import router as city_router

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="Hotel Price Tracker API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class HotelSearch(BaseModel):
    location_id: str
    location_name: str
    check_in: str
    check_out: str
    guests: int = 2
    rooms: int = 1

class PriceAlertRequest(BaseModel):
    hotel_id: str
    target_price: float
    alert_type: str  # 'sms', 'email', or 'both'

class LocationResponse(BaseModel):
    id: str
    name: str
    city: Optional[str]
    country: str
    state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    timezone: Optional[str]

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/locations/search")
async def search_locations(
    query: str,
    limit: int = 10
) -> List[LocationResponse]:
    """Search for cities/locations"""
    try:
        location_service = LocationService()
        locations = await location_service.search_cities(query)
        await location_service.close()
        return locations[:limit]
    except Exception as e:
        logger.error(f"Location search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations/popular")
async def get_popular_locations() -> List[Dict]:
    """Get list of popular destinations"""
    try:
        location_service = LocationService()
        locations = await location_service.get_popular_destinations()
        await location_service.close()
        return locations
    except Exception as e:
        logger.error(f"Error getting popular locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_hotels(
    search: HotelSearch,
    db: Session = Depends(get_db)
):
    try:
        # Convert string dates to datetime
        check_in = datetime.strptime(search.check_in, "%Y-%m-%d")
        check_out = datetime.strptime(search.check_out, "%Y-%m-%d")
        
        # Initialize aggregator
        aggregator = HotelAggregator(db)
        
        # Search across all providers
        hotels = await aggregator.search_all_providers(
            location_id=search.location_id,
            location_name=search.location_name,
            check_in=check_in,
            check_out=check_out,
            guests=search.guests,
            rooms=search.rooms
        )
        
        # Store hotels in database
        for hotel_data in hotels:
            hotel = db.query(Hotel).filter(Hotel.hotel_id == hotel_data['hotel_id']).first()
            if not hotel:
                hotel = Hotel(
                    hotel_id=hotel_data['hotel_id'],
                    name=hotel_data['name'],
                    location=hotel_data['location'],
                    rating=hotel_data.get('rating'),
                    image_url=hotel_data.get('image_url')
                )
                db.add(hotel)
                
        db.commit()
        return hotels
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await aggregator.close()

@app.post("/api/alerts")
async def create_price_alert(
    alert: PriceAlertRequest,
    db: Session = Depends(get_db),
    user_id: int = 1  # Replace with actual user authentication
):
    try:
        hotel = db.query(Hotel).filter(Hotel.hotel_id == alert.hotel_id).first()
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
            
        price_alert = PriceAlert(
            user_id=user_id,
            hotel_id=hotel.id,
            target_price=alert.target_price,
            alert_type=alert.alert_type
        )
        db.add(price_alert)
        db.commit()
        
        return {"message": "Price alert created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hotel/{hotel_id}/prices")
async def get_hotel_prices(
    hotel_id: str,
    check_in: str,
    check_out: str,
    guests: int = 2,
    rooms: int = 1,
    db: Session = Depends(get_db)
):
    try:
        # Convert string dates to datetime
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        
        # Initialize aggregator
        aggregator = HotelAggregator(db)
        
        # Get best price across all providers
        best_price = await aggregator.get_best_price(
            hotel_id=hotel_id,
            check_in=check_in_date,
            check_out=check_out_date,
            guests=guests,
            rooms=rooms
        )
        
        if not best_price:
            raise HTTPException(status_code=404, detail="No prices found")
            
        return best_price
        
    except Exception as e:
        logger.error(f"Error getting prices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await aggregator.close()

@app.get("/api/hotel/{hotel_id}")
async def get_hotel_details(
    hotel_id: str,
    db: Session = Depends(get_db)
):
    try:
        # Initialize aggregator
        aggregator = HotelAggregator(db)
        
        # Get hotel details from first available provider
        for provider in aggregator.providers.values():
            details = await provider.get_hotel_details(hotel_id)
            if details:
                return details
                
        raise HTTPException(status_code=404, detail="Hotel not found")
        
    except Exception as e:
        logger.error(f"Error getting hotel details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await aggregator.close()

app.include_router(analytics_router)
app.include_router(city_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
