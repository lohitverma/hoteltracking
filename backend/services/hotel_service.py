from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp
import asyncio
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from models import Hotel, PriceHistory
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class HotelService:
    def __init__(self, db: Session, cache_service: CacheService):
        self.db = db
        self.cache_service = cache_service
        self.api_key = "YOUR_HOTEL_API_KEY"  # Replace with actual API key
        
    async def search_hotels(
        self,
        city: str,
        check_in: datetime,
        check_out: datetime,
        guests: int = 2,
        rooms: int = 1,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        amenities: Optional[List[str]] = None,
        min_rating: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for hotels using external API and cache results"""
        cache_key = f"hotel_search:{city}:{check_in.date()}:{check_out.date()}:{guests}:{rooms}"
        
        # Try to get from cache
        cached_results = await self.cache_service.get(cache_key)
        if cached_results:
            return cached_results
            
        # Fetch from API
        async with aiohttp.ClientSession() as session:
            params = {
                "city": city,
                "checkin": check_in.strftime("%Y-%m-%d"),
                "checkout": check_out.strftime("%Y-%m-%d"),
                "guests": guests,
                "rooms": rooms,
                "apikey": self.api_key
            }
            
            async with session.get("https://hotel-api.example.com/search", params=params) as response:
                if response.status != 200:
                    raise Exception(f"Hotel API error: {await response.text()}")
                    
                data = await response.json()
                
                # Filter results
                hotels = data.get("hotels", [])
                if min_price:
                    hotels = [h for h in hotels if h["price"] >= min_price]
                if max_price:
                    hotels = [h for h in hotels if h["price"] <= max_price]
                if min_rating:
                    hotels = [h for h in hotels if h.get("rating", 0) >= min_rating]
                if amenities:
                    hotels = [h for h in hotels if all(a in h.get("amenities", []) for a in amenities)]
                
                # Store in database
                for hotel_data in hotels:
                    await self._store_hotel(hotel_data)
                
                # Cache results
                await self.cache_service.set(cache_key, hotels, ttl=timedelta(hours=1))
                
                return hotels
                
    async def _store_hotel(self, hotel_data: Dict[str, Any]):
        """Store or update hotel in database"""
        hotel = self.db.query(Hotel).filter(Hotel.name == hotel_data["name"]).first()
        
        if not hotel:
            hotel = Hotel(
                name=hotel_data["name"],
                city=hotel_data["city"],
                description=hotel_data.get("description", ""),
                amenities=hotel_data.get("amenities", []),
                rating=hotel_data.get("rating"),
                current_price=hotel_data["price"]
            )
            self.db.add(hotel)
        else:
            hotel.current_price = hotel_data["price"]
            hotel.rating = hotel_data.get("rating", hotel.rating)
            hotel.amenities = hotel_data.get("amenities", hotel.amenities)
            
        # Add price history
        price_history = PriceHistory(
            hotel=hotel,
            price=hotel_data["price"]
        )
        self.db.add(price_history)
        
        self.db.commit()
        
    async def get_hotel(self, hotel_id: int) -> Optional[Dict[str, Any]]:
        """Get hotel details by ID"""
        hotel = self.db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            return None
            
        return {
            "id": hotel.id,
            "name": hotel.name,
            "city": hotel.city,
            "description": hotel.description,
            "amenities": hotel.amenities,
            "rating": hotel.rating,
            "current_price": hotel.current_price
        }
        
    async def get_price_history(
        self,
        hotel_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get price history for a hotel"""
        cache_key = f"price_history:{hotel_id}:{days}"
        
        # Try to get from cache
        cached_results = await self.cache_service.get(cache_key)
        if cached_results:
            return cached_results
            
        # Get from database
        since = datetime.utcnow() - timedelta(days=days)
        history = self.db.query(PriceHistory).filter(
            PriceHistory.hotel_id == hotel_id,
            PriceHistory.timestamp >= since
        ).order_by(desc(PriceHistory.timestamp)).all()
        
        results = [
            {
                "price": h.price,
                "timestamp": h.timestamp.isoformat()
            }
            for h in history
        ]
        
        # Cache results
        await self.cache_service.set(cache_key, results, ttl=timedelta(minutes=30))
        
        return results
        
    async def analyze_price_trends(
        self,
        hotel_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze price trends for a hotel"""
        history = await self.get_price_history(hotel_id, days)
        if not history:
            return {
                "trend": "unknown",
                "price_change": 0,
                "price_change_percent": 0,
                "min_price": 0,
                "max_price": 0,
                "avg_price": 0
            }
            
        prices = [h["price"] for h in history]
        current_price = prices[0]
        oldest_price = prices[-1]
        
        return {
            "trend": "up" if current_price > oldest_price else "down",
            "price_change": current_price - oldest_price,
            "price_change_percent": ((current_price - oldest_price) / oldest_price) * 100,
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) / len(prices)
        }
        
    async def get_recommendations(
        self,
        city: str,
        budget: float,
        preferences: List[str]
    ) -> List[Dict[str, Any]]:
        """Get hotel recommendations based on preferences"""
        # Get all hotels in city within budget
        hotels = self.db.query(Hotel).filter(
            Hotel.city == city,
            Hotel.current_price <= budget
        ).all()
        
        # Score hotels based on preferences
        scored_hotels = []
        for hotel in hotels:
            score = 0
            for pref in preferences:
                if pref in hotel.amenities:
                    score += 1
                    
            if score > 0:
                scored_hotels.append({
                    "hotel": hotel,
                    "score": score
                })
                
        # Sort by score and return top 5
        scored_hotels.sort(key=lambda x: (-x["score"], x["hotel"].current_price))
        
        return [
            {
                "id": h["hotel"].id,
                "name": h["hotel"].name,
                "city": h["hotel"].city,
                "price": h["hotel"].current_price,
                "rating": h["hotel"].rating,
                "amenities": h["hotel"].amenities,
                "match_score": h["score"]
            }
            for h in scored_hotels[:5]
        ]
