"""
Hotels.com API Integration
"""
from typing import Dict, List, Optional
from datetime import datetime
import requests
from .base import BaseHotelAPI

class HotelsComAPI(BaseHotelAPI):
    """Hotels.com API client implementation"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://hotels.com/api/v3"
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def search_hotels(
        self,
        location_id: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        rooms: int = 1
    ) -> List[Dict]:
        """
        Search for hotels using Hotels.com API
        
        Args:
            location_id: Location ID to search in
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            rooms: Number of rooms
            
        Returns:
            List of hotel results
        """
        endpoint = f"{self.base_url}/properties/search"
        params = {
            "destination_id": location_id,
            "check_in": check_in,
            "check_out": check_out,
            "rooms": rooms,
            "adults": guests
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._normalize_hotels(data["properties"])
        except Exception as e:
            self.logger.error(f"Error searching hotels: {str(e)}")
            return []

    def get_hotel_details(self, hotel_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific hotel
        
        Args:
            hotel_id: Hotel ID to get details for
            
        Returns:
            Hotel details or None if not found
        """
        endpoint = f"{self.base_url}/properties/{hotel_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return self._normalize_hotel_details(data["property"])
        except Exception as e:
            self.logger.error(f"Error getting hotel details: {str(e)}")
            return None

    def _normalize_hotels(self, hotels: List[Dict]) -> List[Dict]:
        """Normalize hotel data to common format"""
        normalized = []
        for hotel in hotels:
            normalized.append({
                "id": str(hotel["property_id"]),
                "name": hotel["name"],
                "description": hotel.get("description", ""),
                "address": {
                    "street": hotel.get("address", {}).get("street", ""),
                    "city": hotel.get("address", {}).get("city", ""),
                    "country": hotel.get("address", {}).get("country", ""),
                    "postal_code": hotel.get("address", {}).get("postal_code", "")
                },
                "rating": float(hotel.get("star_rating", 0)),
                "price": {
                    "amount": float(hotel["price"]["nightly_price"]),
                    "currency": hotel["price"]["currency"]
                },
                "amenities": hotel.get("amenities", []),
                "images": [img["url"] for img in hotel.get("images", [])]
            })
        return normalized

    def _normalize_hotel_details(self, hotel: Dict) -> Dict:
        """Normalize hotel details to common format"""
        return {
            "id": str(hotel["property_id"]),
            "name": hotel["name"],
            "description": hotel.get("description", ""),
            "address": {
                "street": hotel.get("address", {}).get("street", ""),
                "city": hotel.get("address", {}).get("city", ""),
                "country": hotel.get("address", {}).get("country", ""),
                "postal_code": hotel.get("address", {}).get("postal_code", "")
            },
            "rating": float(hotel.get("star_rating", 0)),
            "amenities": hotel.get("amenities", []),
            "images": [img["url"] for img in hotel.get("images", [])],
            "rooms": [{
                "id": str(room["room_id"]),
                "name": room["name"],
                "description": room.get("description", ""),
                "max_occupancy": room.get("max_occupancy", 2),
                "price": {
                    "amount": float(room["price"]["nightly_price"]),
                    "currency": room["price"]["currency"]
                }
            } for room in hotel.get("rooms", [])]
        }
