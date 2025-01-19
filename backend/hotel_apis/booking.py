"""
Booking.com API Integration
"""
from typing import Dict, List, Optional
from datetime import datetime
import requests
from .base import BaseHotelAPI

class BookingAPI(BaseHotelAPI):
    """Booking.com API client implementation"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://distribution-xml.booking.com/json/bookings"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
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
        Search for hotels using Booking.com API
        
        Args:
            location_id: Location ID to search in
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            rooms: Number of rooms
            
        Returns:
            List of hotel results
        """
        endpoint = f"{self.base_url}/hotels/search"
        params = {
            "city_ids": location_id,
            "checkin": check_in,
            "checkout": check_out,
            "room_number": rooms,
            "guest_number": guests
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._normalize_hotels(data["hotels"])
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
        endpoint = f"{self.base_url}/hotels/{hotel_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return self._normalize_hotel_details(data["hotel"])
        except Exception as e:
            self.logger.error(f"Error getting hotel details: {str(e)}")
            return None

    def _normalize_hotels(self, hotels: List[Dict]) -> List[Dict]:
        """Normalize hotel data to common format"""
        normalized = []
        for hotel in hotels:
            normalized.append({
                "id": str(hotel["hotel_id"]),
                "name": hotel["name"],
                "description": hotel.get("description", ""),
                "address": {
                    "street": hotel.get("address", ""),
                    "city": hotel.get("city", ""),
                    "country": hotel.get("country", ""),
                    "postal_code": hotel.get("zip", "")
                },
                "rating": float(hotel.get("review_score", 0)),
                "price": {
                    "amount": float(hotel["price"]["amount"]),
                    "currency": hotel["price"]["currency"]
                },
                "amenities": hotel.get("facilities", []),
                "images": [img["url"] for img in hotel.get("photos", [])]
            })
        return normalized

    def _normalize_hotel_details(self, hotel: Dict) -> Dict:
        """Normalize hotel details to common format"""
        return {
            "id": str(hotel["hotel_id"]),
            "name": hotel["name"],
            "description": hotel.get("description", ""),
            "address": {
                "street": hotel.get("address", ""),
                "city": hotel.get("city", ""),
                "country": hotel.get("country", ""),
                "postal_code": hotel.get("zip", "")
            },
            "rating": float(hotel.get("review_score", 0)),
            "amenities": hotel.get("facilities", []),
            "images": [img["url"] for img in hotel.get("photos", [])],
            "rooms": [{
                "id": str(room["room_id"]),
                "name": room["name"],
                "description": room.get("description", ""),
                "max_occupancy": room.get("max_occupancy", 2),
                "price": {
                    "amount": float(room["price"]["amount"]),
                    "currency": room["price"]["currency"]
                }
            } for room in hotel.get("rooms", [])]
        }
