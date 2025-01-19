from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import os

class PriceAnalyzer:
    def __init__(self):
        self.model_path = "models/price_predictor.joblib"
        self.scaler_path = "models/price_scaler.joblib"
        self._load_or_train_model()

    def _load_or_train_model(self):
        """Load existing model or train a new one if not exists."""
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
        except FileNotFoundError:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.scaler = StandardScaler()

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for model training/prediction."""
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_holiday'] = self._check_holidays(df['date'])
        
        # Add seasonal features
        df['season'] = df['date'].dt.month.map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'fall', 10: 'fall', 11: 'fall'
        })
        
        # One-hot encode categorical variables
        df = pd.get_dummies(df, columns=['season'])
        
        return df

    def _check_holidays(self, dates: pd.Series) -> pd.Series:
        """Check if dates are holidays (simplified version)."""
        # Add your holiday checking logic here
        return pd.Series([0] * len(dates))

    def train_model(self, historical_data: pd.DataFrame):
        """Train the price prediction model."""
        df = self.prepare_features(historical_data)
        
        X = df.drop(['price', 'date'], axis=1)
        y = df['price']
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        
        # Save model and scaler
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

    def predict_prices(
        self,
        hotel_id: int,
        start_date: datetime,
        days: int = 30
    ) -> List[Dict]:
        """Predict hotel prices for the next N days."""
        dates = [start_date + timedelta(days=i) for i in range(days)]
        df = pd.DataFrame({
            'date': dates,
            'hotel_id': [hotel_id] * days
        })
        
        df = self.prepare_features(df)
        X = df.drop(['date'], axis=1)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        
        return [
            {
                'date': date.strftime('%Y-%m-%d'),
                'predicted_price': round(price, 2)
            }
            for date, price in zip(dates, predictions)
        ]

    def analyze_price_trends(
        self,
        historical_data: pd.DataFrame,
        window: int = 7
    ) -> Dict:
        """Analyze price trends and patterns."""
        df = historical_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate rolling statistics
        rolling_mean = df['price'].rolling(window=window).mean()
        rolling_std = df['price'].rolling(window=window).std()
        
        # Calculate price changes
        df['price_change'] = df['price'].pct_change()
        
        # Identify trends
        trend = 'stable'
        recent_change = df['price_change'].tail(window).mean()
        if recent_change > 0.05:
            trend = 'increasing'
        elif recent_change < -0.05:
            trend = 'decreasing'
        
        # Calculate volatility
        volatility = df['price_change'].std()
        
        # Find seasonal patterns
        seasonal_avg = df.groupby(df['date'].dt.month)['price'].mean()
        peak_month = seasonal_avg.idxmax()
        low_month = seasonal_avg.idxmin()
        
        return {
            'trend': trend,
            'volatility': round(volatility, 4),
            'average_price': round(df['price'].mean(), 2),
            'min_price': round(df['price'].min(), 2),
            'max_price': round(df['price'].max(), 2),
            'peak_month': peak_month,
            'low_month': low_month,
            'rolling_mean': rolling_mean.tolist(),
            'rolling_std': rolling_std.tolist()
        }

    def get_booking_recommendations(
        self,
        predicted_prices: List[Dict],
        budget: Optional[float] = None
    ) -> Dict:
        """Get booking recommendations based on predicted prices."""
        prices = [p['predicted_price'] for p in predicted_prices]
        dates = [p['date'] for p in predicted_prices]
        
        best_price = min(prices)
        best_date = dates[prices.index(best_price)]
        
        price_threshold = budget if budget else np.percentile(prices, 25)
        good_dates = [
            {'date': date, 'price': price}
            for date, price in zip(dates, prices)
            if price <= price_threshold
        ]
        
        return {
            'best_price': round(best_price, 2),
            'best_date': best_date,
            'price_threshold': round(price_threshold, 2),
            'recommended_dates': good_dates,
            'average_price': round(np.mean(prices), 2),
            'price_range': {
                'min': round(min(prices), 2),
                'max': round(max(prices), 2)
            }
        }

# Global analyzer instance
price_analyzer = PriceAnalyzer()
