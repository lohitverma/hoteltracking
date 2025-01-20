from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np
from fastapi import WebSocket
import json

from models import Hotel, PriceHistory
from services.cache_service import CacheService
from services.monitoring_service import MonitoringService

class PriceTrackingService:
    def __init__(self, db: Session, cache_service: CacheService, monitoring_service: MonitoringService):
        self.db = db
        self.cache_service = cache_service
        self.monitoring_service = monitoring_service
        self.active_connections: Dict[str, List[WebSocket]] = {}  # city -> websockets
        self.is_tracking = False

    async def connect_client(self, websocket: WebSocket, city: str):
        await websocket.accept()
        if city not in self.active_connections:
            self.active_connections[city] = []
        self.active_connections[city].append(websocket)
        
        if not self.is_tracking:
            self.is_tracking = True
            asyncio.create_task(self.track_prices())

    async def disconnect_client(self, websocket: WebSocket, city: str):
        if city in self.active_connections:
            self.active_connections[city].remove(websocket)
            if not self.active_connections[city]:
                del self.active_connections[city]

    async def track_prices(self):
        while self.is_tracking and self.active_connections:
            try:
                for city in list(self.active_connections.keys()):
                    prices = await self.get_real_time_prices(city)
                    if prices:
                        # Add timestamp for real-time tracking
                        prices['timestamp'] = datetime.now().isoformat()
                        
                        # Send to all connected clients for this city
                        disconnected = []
                        for websocket in self.active_connections[city]:
                            try:
                                await websocket.send_json(prices)
                            except:
                                disconnected.append(websocket)
                        
                        # Clean up disconnected clients
                        for ws in disconnected:
                            await self.disconnect_client(ws, city)
                
                # Update every 5 minutes
                await asyncio.sleep(300)
            except Exception as e:
                self.monitoring_service.log_error(f"Error in price tracking: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def get_real_time_prices(self, city: str) -> Optional[Dict]:
        """Get real-time prices for all hotels in a city"""
        cache_key = f"real_time_prices_{city}"
        cached_data = await self.cache_service.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)

        try:
            # Get all hotels in the city
            hotels = self.db.query(Hotel).filter(Hotel.city == city).all()
            
            if not hotels:
                return None

            # Get current prices and historical data
            current_prices = {}
            historical_trends = {}
            price_changes = {}
            
            for hotel in hotels:
                # Get price history for last 30 days
                history = (self.db.query(PriceHistory)
                         .filter(PriceHistory.hotel_id == hotel.id)
                         .filter(PriceHistory.date >= datetime.now() - timedelta(days=30))
                         .order_by(PriceHistory.date)
                         .all())
                
                if history:
                    prices = [h.price for h in history]
                    dates = [h.date.isoformat() for h in history]
                    
                    current_prices[hotel.id] = {
                        'hotel_name': hotel.name,
                        'current_price': prices[-1],
                        'min_price': min(prices),
                        'max_price': max(prices),
                        'avg_price': sum(prices) / len(prices)
                    }
                    
                    # Calculate price trends
                    if len(prices) > 1:
                        price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
                        price_changes[hotel.id] = price_change
                    
                    # Store historical data
                    historical_trends[hotel.id] = {
                        'dates': dates,
                        'prices': prices
                    }

            result = {
                'city': city,
                'current_prices': current_prices,
                'historical_trends': historical_trends,
                'price_changes': price_changes,
                'updated_at': datetime.now().isoformat()
            }

            # Cache for 5 minutes
            await self.cache_service.set(cache_key, json.dumps(result), 300)
            
            return result

        except Exception as e:
            self.monitoring_service.log_error(f"Error getting real-time prices: {str(e)}")
            return None

    async def get_price_statistics(self, city: str) -> Dict:
        """Get statistical analysis of hotel prices in a city"""
        try:
            # Get all hotels in the city
            hotels = self.db.query(Hotel).filter(Hotel.city == city).all()
            
            if not hotels:
                return {}

            stats = {
                'city': city,
                'total_hotels': len(hotels),
                'price_ranges': {
                    'budget': {'min': float('inf'), 'max': 0, 'count': 0},
                    'mid_range': {'min': float('inf'), 'max': 0, 'count': 0},
                    'luxury': {'min': float('inf'), 'max': 0, 'count': 0}
                },
                'average_prices': {
                    'overall': 0,
                    'by_rating': {}
                }
            }

            prices = []
            for hotel in hotels:
                latest_price = (self.db.query(PriceHistory)
                              .filter(PriceHistory.hotel_id == hotel.id)
                              .order_by(PriceHistory.date.desc())
                              .first())
                
                if latest_price:
                    price = latest_price.price
                    prices.append(price)
                    
                    # Categorize by price range
                    if price < 100:
                        category = 'budget'
                    elif price < 300:
                        category = 'mid_range'
                    else:
                        category = 'luxury'
                    
                    stats['price_ranges'][category]['min'] = min(
                        stats['price_ranges'][category]['min'], price)
                    stats['price_ranges'][category]['max'] = max(
                        stats['price_ranges'][category]['max'], price)
                    stats['price_ranges'][category]['count'] += 1
                    
                    # Group by rating
                    rating_key = str(round(hotel.rating))
                    if rating_key not in stats['average_prices']['by_rating']:
                        stats['average_prices']['by_rating'][rating_key] = []
                    stats['average_prices']['by_rating'][rating_key].append(price)

            # Calculate averages
            if prices:
                stats['average_prices']['overall'] = sum(prices) / len(prices)
                for rating, rating_prices in stats['average_prices']['by_rating'].items():
                    stats['average_prices']['by_rating'][rating] = sum(rating_prices) / len(rating_prices)

            return stats

        except Exception as e:
            self.monitoring_service.log_error(f"Error getting price statistics: {str(e)}")
            return {}
