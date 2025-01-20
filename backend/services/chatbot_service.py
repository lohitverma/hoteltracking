from typing import List, Dict, Any, Optional
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
import spacy
import numpy as np
from datetime import datetime

from models import Hotel
from services.hotel_service import HotelService

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self, db: Session, hotel_service: HotelService):
        self.db = db
        self.hotel_service = hotel_service
        # Load English language model
        self.nlp = spacy.load("en_core_web_sm")
        
    async def get_response(self, message: str) -> Dict[str, Any]:
        """Process user message and return appropriate response"""
        # Analyze message intent
        doc = self.nlp(message.lower())
        
        # Extract key information
        info = self._extract_info(doc)
        
        # Handle different intents
        if self._is_price_query(doc):
            return await self._handle_price_query(info)
        elif self._is_recommendation_query(doc):
            return await self._handle_recommendation_query(info)
        elif self._is_amenity_query(doc):
            return await self._handle_amenity_query(info)
        else:
            return {
                "type": "text",
                "content": "I can help you find hotels, check prices, and give recommendations. Try asking something like:\n"
                          "- What are the best hotels in New York under $200?\n"
                          "- Find hotels with a pool in Miami\n"
                          "- Show me price trends for Hilton downtown"
            }
            
    def _extract_info(self, doc) -> Dict[str, Any]:
        """Extract relevant information from the message"""
        info = {
            "city": None,
            "price_max": None,
            "amenities": [],
            "hotel_name": None
        }
        
        # Extract city names
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Geographical Entity
                info["city"] = ent.text
                break
                
        # Extract price
        price_pattern = r'\$(\d+)'
        price_matches = re.findall(price_pattern, doc.text)
        if price_matches:
            info["price_max"] = float(price_matches[0])
            
        # Extract amenities
        amenities = [
            "pool", "gym", "spa", "restaurant", "bar", "wifi",
            "parking", "beach", "breakfast", "room service"
        ]
        info["amenities"] = [word.text for word in doc 
                           if word.text.lower() in amenities]
                           
        # Extract hotel name (look for proper nouns near "hotel")
        for token in doc:
            if token.text.lower() == "hotel":
                # Look at nearby proper nouns
                for nearby in token.nbor():
                    if nearby.pos_ == "PROPN":
                        info["hotel_name"] = nearby.text
                        
        return info
        
    def _is_price_query(self, doc) -> bool:
        """Check if message is asking about prices"""
        price_keywords = ["price", "cost", "rate", "cheap", "expensive"]
        return any(token.text.lower() in price_keywords for token in doc)
        
    def _is_recommendation_query(self, doc) -> bool:
        """Check if message is asking for recommendations"""
        rec_keywords = ["recommend", "suggest", "best", "top", "find", "search"]
        return any(token.text.lower() in rec_keywords for token in doc)
        
    def _is_amenity_query(self, doc) -> bool:
        """Check if message is asking about amenities"""
        amenity_keywords = ["have", "offer", "amenity", "feature"]
        return any(token.text.lower() in amenity_keywords for token in doc)
        
    async def _handle_price_query(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries about hotel prices"""
        if info["hotel_name"]:
            # Get specific hotel price
            hotel = self.db.query(Hotel).filter(
                func.lower(Hotel.name).contains(info["hotel_name"].lower())
            ).first()
            
            if hotel:
                trends = await self.hotel_service.analyze_price_trends(hotel.id)
                return {
                    "type": "price_info",
                    "content": {
                        "hotel": {
                            "name": hotel.name,
                            "current_price": hotel.current_price,
                            "rating": hotel.rating
                        },
                        "trends": trends
                    }
                }
        elif info["city"]:
            # Get price range for city
            hotels = self.db.query(Hotel).filter(
                func.lower(Hotel.city) == info["city"].lower()
            ).all()
            
            if hotels:
                prices = [h.current_price for h in hotels]
                return {
                    "type": "price_range",
                    "content": {
                        "city": info["city"],
                        "min_price": min(prices),
                        "max_price": max(prices),
                        "avg_price": sum(prices) / len(prices)
                    }
                }
                
        return {
            "type": "text",
            "content": "I couldn't find price information for your query. "
                      "Please specify a city or hotel name."
        }
        
    async def _handle_recommendation_query(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries asking for hotel recommendations"""
        if not info["city"]:
            return {
                "type": "text",
                "content": "Please specify a city for hotel recommendations."
            }
            
        # Get recommendations
        budget = info["price_max"] if info["price_max"] else float('inf')
        preferences = info["amenities"]
        
        recommendations = await self.hotel_service.get_recommendations(
            info["city"],
            budget,
            preferences
        )
        
        if recommendations:
            return {
                "type": "recommendations",
                "content": {
                    "city": info["city"],
                    "hotels": recommendations
                }
            }
        else:
            return {
                "type": "text",
                "content": f"I couldn't find any hotels in {info['city']} matching your criteria."
            }
            
    async def _handle_amenity_query(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries about hotel amenities"""
        if info["hotel_name"]:
            hotel = self.db.query(Hotel).filter(
                func.lower(Hotel.name).contains(info["hotel_name"].lower())
            ).first()
            
            if hotel:
                return {
                    "type": "amenities",
                    "content": {
                        "hotel": hotel.name,
                        "amenities": hotel.amenities
                    }
                }
        elif info["city"] and info["amenities"]:
            # Find hotels with specific amenities
            hotels = self.db.query(Hotel).filter(
                func.lower(Hotel.city) == info["city"].lower()
            ).all()
            
            matching_hotels = [
                {
                    "name": h.name,
                    "amenities": h.amenities,
                    "price": h.current_price,
                    "rating": h.rating
                }
                for h in hotels
                if all(a in h.amenities for a in info["amenities"])
            ]
            
            if matching_hotels:
                return {
                    "type": "hotel_amenities",
                    "content": {
                        "city": info["city"],
                        "amenities": info["amenities"],
                        "hotels": matching_hotels
                    }
                }
                
        return {
            "type": "text",
            "content": "I couldn't find amenity information for your query. "
                      "Please specify a hotel name or city and amenities."
        }
