"""
Hotel APIs Package
"""
from .base import BaseHotelAPI
from .expedia import ExpediaAPI
from .booking import BookingAPI
from .hotels import HotelsComAPI
from .amadeus import AmadeusAPI

__all__ = ['BaseHotelAPI', 'ExpediaAPI', 'BookingAPI', 'HotelsComAPI', 'AmadeusAPI']
