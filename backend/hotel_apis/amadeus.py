"""
Amadeus API Integration
"""
from typing import Dict, List, Optional
from datetime import datetime
import requests
from .base import BaseHotelAPI

class AmadeusAPI(BaseHotelAPI):
    """Amadeus API client implementation"""
    
    def __init__(self, api_key: str, api_secret: str):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.amadeus.com/v2"
        self.token = None
        self._authenticate()

    def _authenticate(self):
        """Get access token from Amadeus"""
        auth_url = "https://api.amadeus.com/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            response = requests.post(auth_url, data=data)
            response.raise_for_status()
            self.token = response.json()["access_token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        except Exception as e:
            self.logger.error(f"Error authenticating with Amadeus: {str(e)}")
            raise

    def search_hotels(
        self,
        location_id: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        rooms: int = 1
    ) -> List[Dict]:
        """
        Search for hotels using Amadeus API
        
        Args:
            location_id: Location ID to search in
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            rooms: Number of rooms
            
        Returns:
            List of hotel results
        """
        endpoint = f"{self.base_url}/shopping/hotel-offers"
        params = {
            "cityCode": location_id,
            "checkInDate": check_in,
            "checkOutDate": check_out,
            "adults": guests,
            "roomQuantity": rooms
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._normalize_hotels(data["data"])
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
        endpoint = f"{self.base_url}/shopping/hotel-offers/by-hotel"
        params = {"hotelId": hotel_id}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._normalize_hotel_details(data["data"])
        except Exception as e:
            self.logger.error(f"Error getting hotel details: {str(e)}")
            return None

    def _normalize_hotels(self, hotels: List[Dict]) -> List[Dict]:
        """Normalize hotel data to common format"""
        normalized = []
        for hotel in hotels:
            hotel_data = hotel["hotel"]
            offer = hotel["offers"][0] if hotel.get("offers") else {}
            
            normalized.append({
                "id": str(hotel_data["hotelId"]),
                "name": hotel_data["name"],
                "description": hotel_data.get("description", {}).get("text", ""),
                "address": {
                    "street": hotel_data.get("address", {}).get("lines", [""])[0],
                    "city": hotel_data.get("address", {}).get("cityName", ""),
                    "country": hotel_data.get("address", {}).get("countryCode", ""),
                    "postal_code": hotel_data.get("address", {}).get("postalCode", "")
                },
                "rating": float(hotel_data.get("rating", 0)),
                "price": {
                    "amount": float(offer.get("price", {}).get("total", 0)),
                    "currency": offer.get("price", {}).get("currency", "USD")
                },
                "amenities": hotel_data.get("amenities", []),
                "images": [media["uri"] for media in hotel_data.get("media", [])]
            })
        return normalized

    def _normalize_hotel_details(self, hotel: Dict) -> Dict:
        """Normalize hotel details to common format"""
        hotel_data = hotel["hotel"]
        offers = hotel.get("offers", [])
        
        return {
            "id": str(hotel_data["hotelId"]),
            "name": hotel_data["name"],
            "description": hotel_data.get("description", {}).get("text", ""),
            "address": {
                "street": hotel_data.get("address", {}).get("lines", [""])[0],
                "city": hotel_data.get("address", {}).get("cityName", ""),
                "country": hotel_data.get("address", {}).get("countryCode", ""),
                "postal_code": hotel_data.get("address", {}).get("postalCode", "")
            },
            "rating": float(hotel_data.get("rating", 0)),
            "amenities": hotel_data.get("amenities", []),
            "images": [media["uri"] for media in hotel_data.get("media", [])],
            "rooms": [{
                "id": str(offer["id"]),
                "name": offer.get("room", {}).get("type", ""),
                "description": offer.get("room", {}).get("description", {}).get("text", ""),
                "max_occupancy": offer.get("guests", {}).get("adults", 2),
                "price": {
                    "amount": float(offer.get("price", {}).get("total", 0)),
                    "currency": offer.get("price", {}).get("currency", "USD")
                }
            } for offer in offers]
        }
