from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Hotel(Base):
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(String, unique=True, index=True)
    name = Column(String)
    location = Column(String)
    rating = Column(Float)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    amenities = Column(JSON)
    description = Column(Text)
    coordinates = Column(JSON)  # {lat: float, lng: float}

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(String, ForeignKey("hotels.hotel_id"))
    price = Column(Float)
    currency = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    provider = Column(String)
    room_type = Column(String)

class City(Base):
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    country = Column(String)
    state = Column(String, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String)
    population = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
