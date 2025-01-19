from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone_number = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON)
    
    alerts = relationship("PriceAlert", back_populates="user")
    searches = relationship("SearchHistory", back_populates="user")

class Hotel(Base):
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(String, unique=True, index=True)
    name = Column(String)
    location = Column(String)
    rating = Column(Float)
    amenities = Column(JSON)
    image_url = Column(String)
    
    price_history = relationship("PriceHistory", back_populates="hotel")
    alerts = relationship("PriceAlert", back_populates="hotel")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    price = Column(Float)
    currency = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    hotel = relationship("Hotel", back_populates="price_history")

class PriceAlert(Base):
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    target_price = Column(Float)
    is_active = Column(Boolean, default=True)
    alert_type = Column(String)  # 'sms', 'email', or 'both'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="alerts")
    hotel = relationship("Hotel", back_populates="alerts")

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    search_query = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="searches")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)
    event_data = Column(JSON)
    user_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String)
