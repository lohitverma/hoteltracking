from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from hotel_apis import ExpediaAPI, BookingAPI, HotelsComAPI, AmadeusAPI
from models import Hotel, PriceHistory
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class HotelAggregator:
    """Aggregates hotel data from multiple providers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.providers = {}
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize API clients for each provider"""
        try:
            self.providers = {
                'expedia': ExpediaAPI(
                    api_key=os.getenv('EXPEDIA_API_KEY'),
                    api_secret=os.getenv('EXPEDIA_API_SECRET')
                ),
                'booking': BookingAPI(
                    api_key=os.getenv('BOOKING_API_KEY')
                ),
                'hotels': HotelsComAPI(
                    api_key=os.getenv('HOTELS_API_KEY')
                ),
                'amadeus': AmadeusAPI(
                    api_key=os.getenv('AMADEUS_API_KEY'),
                    api_secret=os.getenv('AMADEUS_API_SECRET')
                )
            }
        except Exception as e:
            logger.error(f"Error initializing providers: {str(e)}")
            
    async def search_all_providers(
        self,
        location: str,
        check_in: datetime,
        check_out: datetime,
        guests: int,
        rooms: int = 1
    ) -> List[Dict]:
        """Search for hotels across all providers"""
        
        tasks = []
        for provider in self.providers.values():
            tasks.append(
                provider.search_hotels(
                    location=location,
                    check_in=check_in,
                    check_out=check_out,
                    guests=guests,
                    rooms=rooms
                )
            )
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        hotels = {}
        for provider_results in results:
            if isinstance(provider_results, Exception):
                continue
                
            for hotel in provider_results:
                hotel_id = hotel['hotel_id']
                if hotel_id not in hotels:
                    hotels[hotel_id] = hotel
                else:
                    # Update with lowest price
                    if hotel['price'] < hotels[hotel_id]['price']:
                        hotels[hotel_id].update(hotel)
                        
        return list(hotels.values())
        
    async def get_best_price(
        self,
        hotel_id: str,
        check_in: datetime,
        check_out: datetime,
        guests: int,
        rooms: int = 1
    ) -> Optional[Dict]:
        """Get the best price for a hotel across all providers"""
        
        tasks = []
        for provider in self.providers.values():
            tasks.append(
                provider.get_room_rates(
                    hotel_id=hotel_id,
                    check_in=check_in,
                    check_out=check_out,
                    guests=guests,
                    rooms=rooms
                )
            )
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find the lowest price
        best_price = None
        for provider_results in results:
            if isinstance(provider_results, Exception) or not provider_results:
                continue
                
            for rate in provider_results:
                if not best_price or rate.price < best_price.price:
                    best_price = rate
                    
        return best_price
        
    async def track_price_changes(self, hotel_id: str):
        """Track price changes for a hotel"""
        
        hotel = self.db.query(Hotel).filter(Hotel.hotel_id == hotel_id).first()
        if not hotel:
            return
            
        # Get current price
        best_price = await self.get_best_price(
            hotel_id=hotel_id,
            check_in=datetime.now(),
            check_out=datetime.now(),
            guests=2
        )
        
        if best_price:
            # Record price history
            price_history = PriceHistory(
                hotel_id=hotel.id,
                price=best_price.price,
                currency=best_price.currency,
                provider=best_price.provider
            )
            self.db.add(price_history)
            self.db.commit()
            
    async def close(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            await provider.close()
