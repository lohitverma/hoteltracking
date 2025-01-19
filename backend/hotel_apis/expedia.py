import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseHotelAPI, HotelPrice
import os
import json
import logging

logger = logging.getLogger(__name__)

class ExpediaAPI(BaseHotelAPI):
    """Expedia API Integration"""
    
    BASE_URL = "https://hotels.api.expedia.com/v3"
    
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret)
        self.session = None
        
    async def _ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
    async def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        await self._ensure_session()
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with self.session.request(method, url, json=data) as response:
                response_data = await response.json()
                if not self.validate_response(response_data):
                    logger.error(f"Expedia API error: {response_data.get('error')}")
                    return None
                return response_data
        except Exception as e:
            logger.error(f"Error making Expedia API request: {str(e)}")
            return None
            
    async def search_hotels(
        self,
        location: str,
        check_in: datetime,
        check_out: datetime,
        guests: int,
        rooms: int = 1
    ) -> List[Dict]:
        """Search for hotels on Expedia"""
        
        data = {
            "destination": {
                "regionId": location
            },
            "dates": {
                "checkin": self.format_date(check_in),
                "checkout": self.format_date(check_out)
            },
            "rooms": [{
                "adults": guests,
                "children": []
            }] * rooms,
            "resultsStartingIndex": 0,
            "resultsSize": 50,
            "sort": "PRICE",
            "filters": {
                "price": {
                    "max": 5000,
                    "min": 0
                }
            }
        }
        
        response = await self._make_request("properties/search", "POST", data)
        if not response:
            return []
            
        return [
            {
                "hotel_id": hotel["id"],
                "name": hotel["name"],
                "location": hotel["location"]["address"]["cityName"],
                "price": hotel["price"]["lead"]["amount"],
                "currency": hotel["price"]["lead"]["currency"],
                "rating": hotel.get("rating", {}).get("value"),
                "image_url": hotel.get("propertyImage", {}).get("image", {}).get("url"),
                "provider": "Expedia"
            }
            for hotel in response.get("properties", [])
        ]
        
    async def get_hotel_details(self, hotel_id: str) -> Dict:
        """Get detailed information about a specific hotel from Expedia"""
        
        response = await self._make_request(f"properties/{hotel_id}")
        if not response:
            return None
            
        return {
            "hotel_id": response["id"],
            "name": response["name"],
            "description": response.get("description", ""),
            "amenities": [
                amenity["name"]
                for amenity in response.get("amenities", [])
            ],
            "images": [
                image["url"]
                for image in response.get("propertyGallery", {}).get("images", [])
            ],
            "address": response["location"]["address"],
            "rating": response.get("rating", {}).get("value"),
            "provider": "Expedia"
        }
        
    async def get_room_rates(
        self,
        hotel_id: str,
        check_in: datetime,
        check_out: datetime,
        guests: int,
        rooms: int = 1
    ) -> List[HotelPrice]:
        """Get room rates for a specific hotel from Expedia"""
        
        data = {
            "dates": {
                "checkin": self.format_date(check_in),
                "checkout": self.format_date(check_out)
            },
            "rooms": [{
                "adults": guests,
                "children": []
            }] * rooms
        }
        
        response = await self._make_request(
            f"properties/{hotel_id}/availability",
            "POST",
            data
        )
        
        if not response:
            return []
            
        return [
            HotelPrice(
                provider="Expedia",
                price=rate["price"]["lead"]["amount"],
                currency=rate["price"]["lead"]["currency"],
                room_type=rate["name"],
                board_type=rate.get("boardType"),
                cancellation_policy=rate.get("cancellationPolicy", {}).get("description"),
                timestamp=datetime.utcnow(),
                url=f"https://www.expedia.com/hotel/{hotel_id}"
            )
            for rate in response.get("rates", [])
        ]
        
    async def get_availability(
        self,
        hotel_id: str,
        check_in: datetime,
        check_out: datetime
    ) -> bool:
        """Check if hotel is available on Expedia for given dates"""
        
        data = {
            "dates": {
                "checkin": self.format_date(check_in),
                "checkout": self.format_date(check_out)
            },
            "rooms": [{"adults": 1}]
        }
        
        response = await self._make_request(
            f"properties/{hotel_id}/availability",
            "POST",
            data
        )
        
        return bool(response and response.get("rates"))
        
    async def close(self):
        """Close the API session"""
        if self.session:
            await self.session.close()
            self.session = None
