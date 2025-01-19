from typing import List, Dict
import aiohttp
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LocationService:
    """Service for location search and validation"""
    
    def __init__(self):
        self.session = None
        self.api_key = os.getenv('AMADEUS_API_KEY')
        self.api_secret = os.getenv('AMADEUS_API_SECRET')
        self.token = None
        self.token_expiry = None
        
    async def _ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def _get_token(self):
        """Get Amadeus API token"""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        await self._ensure_session()
        
        try:
            async with self.session.post(
                'https://test.api.amadeus.com/v1/security/oauth2/token',
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.api_key,
                    'client_secret': self.api_secret
                }
            ) as response:
                data = await response.json()
                self.token = data['access_token']
                # Token expires in 30 minutes, we'll refresh after 25
                self.token_expiry = datetime.now() + datetime.timedelta(minutes=25)
                return self.token
        except Exception as e:
            logger.error(f"Error getting Amadeus token: {str(e)}")
            return None
            
    async def search_cities(self, query: str) -> List[Dict]:
        """Search for cities matching the query"""
        try:
            token = await self._get_token()
            if not token:
                return []
                
            await self._ensure_session()
            
            async with self.session.get(
                'https://test.api.amadeus.com/v1/reference-data/locations',
                params={
                    'subType': 'CITY',
                    'keyword': query,
                    'page[limit]': 10
                },
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                data = await response.json()
                
                return [
                    {
                        'id': city['id'],
                        'name': city['name'],
                        'city': city.get('address', {}).get('cityName'),
                        'country': city.get('address', {}).get('countryName'),
                        'state': city.get('address', {}).get('stateCode'),
                        'latitude': city.get('geoCode', {}).get('latitude'),
                        'longitude': city.get('geoCode', {}).get('longitude'),
                        'timezone': city.get('timeZone', {}).get('name')
                    }
                    for city in data.get('data', [])
                ]
                
        except Exception as e:
            logger.error(f"Error searching cities: {str(e)}")
            return []
            
    async def get_popular_destinations(self) -> List[Dict]:
        """Get list of popular travel destinations"""
        popular_cities = [
            {"name": "New York", "country": "United States", "id": "NYC"},
            {"name": "London", "country": "United Kingdom", "id": "LON"},
            {"name": "Paris", "country": "France", "id": "PAR"},
            {"name": "Tokyo", "country": "Japan", "id": "TYO"},
            {"name": "Dubai", "country": "United Arab Emirates", "id": "DXB"},
            {"name": "Singapore", "country": "Singapore", "id": "SIN"},
            {"name": "Rome", "country": "Italy", "id": "ROM"},
            {"name": "Barcelona", "country": "Spain", "id": "BCN"},
            {"name": "Sydney", "country": "Australia", "id": "SYD"},
            {"name": "Hong Kong", "country": "China", "id": "HKG"}
        ]
        return popular_cities
        
    async def get_city_details(self, city_id: str) -> Dict:
        """Get detailed information about a specific city"""
        try:
            token = await self._get_token()
            if not token:
                return None
                
            await self._ensure_session()
            
            async with self.session.get(
                f'https://test.api.amadeus.com/v1/reference-data/locations/{city_id}',
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                data = await response.json()
                if 'data' not in data:
                    return None
                    
                city = data['data']
                return {
                    'id': city['id'],
                    'name': city['name'],
                    'city': city.get('address', {}).get('cityName'),
                    'country': city.get('address', {}).get('countryName'),
                    'state': city.get('address', {}).get('stateCode'),
                    'latitude': city.get('geoCode', {}).get('latitude'),
                    'longitude': city.get('geoCode', {}).get('longitude'),
                    'timezone': city.get('timeZone', {}).get('name'),
                    'type': city.get('subType'),
                    'relevance': city.get('relevance')
                }
                
        except Exception as e:
            logger.error(f"Error getting city details: {str(e)}")
            return None

    async def get_city_hotels(self, city_id: str, radius: int = 20) -> List[Dict]:
        """Get hotels in a specific city within given radius (in km)"""
        try:
            token = await self._get_token()
            if not token:
                return []
                
            # First get city coordinates
            city = await self.get_city_details(city_id)
            if not city:
                return []
                
            await self._ensure_session()
            
            # Search for hotels using city coordinates
            async with self.session.get(
                'https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-geocode',
                params={
                    'latitude': city['latitude'],
                    'longitude': city['longitude'],
                    'radius': radius,
                    'radiusUnit': 'KM',
                    'hotelSource': 'ALL'
                },
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                data = await response.json()
                
                return [
                    {
                        'hotel_id': hotel['hotelId'],
                        'name': hotel.get('name'),
                        'distance': hotel.get('distance', {}).get('value'),
                        'rating': hotel.get('rating'),
                        'city_name': city['city'],
                        'country_code': hotel.get('address', {}).get('countryCode'),
                        'latitude': hotel.get('geoCode', {}).get('latitude'),
                        'longitude': hotel.get('geoCode', {}).get('longitude')
                    }
                    for hotel in data.get('data', [])
                ]
                
        except Exception as e:
            logger.error(f"Error getting city hotels: {str(e)}")
            return []

    async def get_city_stats(self, city_id: str) -> Dict:
        """Get statistics about hotels in a city"""
        hotels = await self.get_city_hotels(city_id)
        if not hotels:
            return {
                'total_hotels': 0,
                'avg_rating': None,
                'rating_distribution': {},
                'coverage_area': None
            }
            
        # Calculate statistics
        total_hotels = len(hotels)
        ratings = [h['rating'] for h in hotels if h['rating']]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Calculate rating distribution
        rating_distribution = {}
        for rating in ratings:
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
            
        # Calculate coverage area (rough circle area based on max distance)
        max_distance = max([h['distance'] for h in hotels if h['distance']], default=0)
        coverage_area = 3.14159 * (max_distance ** 2) if max_distance else None
        
        return {
            'total_hotels': total_hotels,
            'avg_rating': round(avg_rating, 2) if avg_rating else None,
            'rating_distribution': rating_distribution,
            'coverage_area': round(coverage_area, 2) if coverage_area else None
        }

    async def close(self):
        """Close the API session"""
        if self.session:
            await self.session.close()
            self.session = None
