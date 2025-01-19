from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

class HotelPrice(BaseModel):
    provider: str
    price: float
    currency: str
    room_type: str
    board_type: Optional[str]
    cancellation_policy: Optional[str]
    timestamp: datetime
    url: str

class BaseHotelAPI(ABC):
    """Base class for hotel API integrations"""
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        
    @abstractmethod
    async def search_hotels(
        self,
        location: str,
        check_in: datetime,
        check_out: datetime,
        guests: int,
        rooms: int = 1
    ) -> List[Dict]:
        """Search for hotels with given criteria"""
        pass
        
    @abstractmethod
    async def get_hotel_details(self, hotel_id: str) -> Dict:
        """Get detailed information about a specific hotel"""
        pass
        
    @abstractmethod
    async def get_room_rates(
        self,
        hotel_id: str,
        check_in: datetime,
        check_out: datetime,
        guests: int,
        rooms: int = 1
    ) -> List[HotelPrice]:
        """Get room rates for a specific hotel"""
        pass
        
    @abstractmethod
    async def get_availability(
        self,
        hotel_id: str,
        check_in: datetime,
        check_out: datetime
    ) -> bool:
        """Check if hotel is available for given dates"""
        pass
        
    def format_date(self, date: datetime) -> str:
        """Format date according to API requirements"""
        return date.strftime("%Y-%m-%d")
        
    def validate_response(self, response: Dict) -> bool:
        """Validate API response"""
        return True if response and not response.get('error') else False
