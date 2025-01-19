from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import PriceHistory, Hotel, Analytics
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_price_history(self, hotel_id: int, days: int = 30) -> List[Dict]:
        """Get price history for a hotel over the specified number of days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        history = (
            self.db.query(PriceHistory)
            .filter(
                PriceHistory.hotel_id == hotel_id,
                PriceHistory.timestamp >= cutoff_date
            )
            .order_by(PriceHistory.timestamp)
            .all()
        )
        
        return [
            {
                "price": h.price,
                "currency": h.currency,
                "timestamp": h.timestamp.isoformat()
            }
            for h in history
        ]

    def get_price_trends(self, hotel_id: int, days: int = 30) -> Dict:
        """Analyze price trends for a hotel"""
        history = self.get_price_history(hotel_id, days)
        
        if not history:
            return {
                "trend": "insufficient_data",
                "avg_price": None,
                "min_price": None,
                "max_price": None,
                "price_volatility": None,
                "forecast": None
            }

        # Convert to pandas DataFrame for analysis
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Basic statistics
        stats = {
            "avg_price": float(df['price'].mean()),
            "min_price": float(df['price'].min()),
            "max_price": float(df['price'].max()),
            "price_volatility": float(df['price'].std()) if len(df) > 1 else 0
        }
        
        # Determine trend
        if len(df) >= 2:
            # Prepare data for regression
            X = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds().values.reshape(-1, 1)
            y = df['price'].values
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Determine trend based on slope
            slope = model.coef_[0]
            if slope > 0.001:  # Price increasing
                trend = "increasing"
            elif slope < -0.001:  # Price decreasing
                trend = "decreasing"
            else:  # Price stable
                trend = "stable"
                
            # Simple price forecast for next 7 days
            future_dates = pd.date_range(
                df['timestamp'].max(),
                periods=8,
                freq='D'
            )[1:]  # Exclude current day
            
            future_seconds = (future_dates - df['timestamp'].min()).total_seconds().values.reshape(-1, 1)
            forecast = model.predict(future_seconds)
            
            stats["forecast"] = [
                {
                    "date": date.isoformat(),
                    "price": float(price)
                }
                for date, price in zip(future_dates, forecast)
            ]
        else:
            trend = "insufficient_data"
            stats["forecast"] = None
            
        stats["trend"] = trend
        return stats

    def get_seasonal_analysis(self, hotel_id: int) -> Dict:
        """Analyze seasonal price patterns"""
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        history = (
            self.db.query(PriceHistory)
            .filter(
                PriceHistory.hotel_id == hotel_id,
                PriceHistory.timestamp >= one_year_ago
            )
            .order_by(PriceHistory.timestamp)
            .all()
        )
        
        if not history:
            return {"seasonal_patterns": "insufficient_data"}
            
        df = pd.DataFrame([
            {
                "price": h.price,
                "timestamp": h.timestamp
            }
            for h in history
        ])
        
        # Group by month and calculate average prices
        df['month'] = df['timestamp'].dt.month
        monthly_avg = df.groupby('month')['price'].mean()
        
        # Find peak and low seasons
        peak_month = monthly_avg.idxmax()
        low_month = monthly_avg.idxmin()
        
        return {
            "seasonal_patterns": {
                "peak_season": {
                    "month": int(peak_month),
                    "avg_price": float(monthly_avg[peak_month])
                },
                "low_season": {
                    "month": int(low_month),
                    "avg_price": float(monthly_avg[low_month])
                },
                "monthly_averages": {
                    int(month): float(avg)
                    for month, avg in monthly_avg.items()
                }
            }
        }

    def get_market_comparison(self, hotel_id: int, location: str) -> Dict:
        """Compare hotel prices with others in the same location"""
        hotel = self.db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            return {"error": "Hotel not found"}
            
        # Get current average price for the hotel
        current_price = (
            self.db.query(func.avg(PriceHistory.price))
            .filter(PriceHistory.hotel_id == hotel_id)
            .scalar()
        )
        
        # Get average prices for hotels in the same location
        location_prices = (
            self.db.query(
                func.avg(PriceHistory.price).label('avg_price'),
                Hotel.rating
            )
            .join(Hotel)
            .filter(Hotel.location == location)
            .group_by(Hotel.id, Hotel.rating)
            .all()
        )
        
        if not location_prices:
            return {"error": "No comparison data available"}
            
        # Calculate market statistics
        prices = [p[0] for p in location_prices if p[0] is not None]
        if not prices:
            return {"error": "No valid prices for comparison"}
            
        market_avg = np.mean(prices)
        percentile = sum(1 for p in prices if p > current_price) / len(prices) * 100
        
        return {
            "current_price": float(current_price),
            "market_average": float(market_avg),
            "price_percentile": float(percentile),
            "comparison": "above_average" if current_price > market_avg else "below_average",
            "difference_percentage": float((current_price - market_avg) / market_avg * 100)
        }

    def record_analytics_event(self, event_type: str, event_data: Dict, user_id: Optional[int] = None, session_id: str = None):
        """Record an analytics event"""
        event = Analytics(
            event_type=event_type,
            event_data=event_data,
            user_id=user_id,
            session_id=session_id
        )
        self.db.add(event)
        self.db.commit()
