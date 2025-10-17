import requests
from datetime import datetime
import pytz
import logging
from config import Config

logger = logging.getLogger(__name__)

class ContextService:
    """Detects and manages contextual information"""
    
    def __init__(self, config=None):
        self.config = config or Config()
    
    def get_time_context(self, timezone='Europe/Moscow'):
        """Get time-based context"""
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        hour = now.hour
        day_of_week = now.strftime('%A')
        
        if 5 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 17:
            time_of_day = 'afternoon'
        elif 17 <= hour < 22:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
        
        return {
            'time_of_day': time_of_day,
            'day_of_week': day_of_week.lower(),
            'hour': hour,
            'is_weekend': day_of_week in ['Saturday', 'Sunday']
        }
    
    def get_weather_context(self, city='Moscow'):
        """Get weather-based context"""
        if not self.config.WEATHER_API_KEY:
            logger.warning("Weather API key not configured")
            return None
        
        try:
            # Get coordinates
            geo_url = self.config.GEOCODING_API_URL
            geo_params = {
                'q': city,
                'limit': 1,
                'appid': self.config.WEATHER_API_KEY
            }
            geo_response = requests.get(geo_url, params=geo_params, timeout=5)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            
            if not geo_data:
                return None
            
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            
            # Get weather
            weather_url = self.config.WEATHER_API_URL
            weather_params = {
                'lat': lat,
                'lon': lon,
                'appid': self.config.WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ru'
            }
            weather_response = requests.get(weather_url, params=weather_params, timeout=5)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
            return {
                'condition': weather_data['weather'][0]['main'].lower(),
                'description': weather_data['weather'][0]['description'],
                'temperature': weather_data['main']['temp'],
                'feels_like': weather_data['main']['feels_like']
            }
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None
    
    def determine_content_preferences(self, context):
        """Determine content preferences based on context"""
        preferences = {
            'genres': [],
            'mood': 'neutral',
            'energy_level': 'medium'
        }
        
        # Time-based preferences
        time_of_day = context.get('time_of_day')
        if time_of_day in self.config.TIME_PREFERENCES:
            preferences['genres'].extend(self.config.TIME_PREFERENCES[time_of_day])
        
        # Weather-based preferences
        weather = context.get('weather')
        if weather and weather.get('condition') in self.config.WEATHER_CONTENT_MAP:
            weather_genres = self.config.WEATHER_CONTENT_MAP[weather['condition']]
            preferences['genres'].extend(weather_genres)
        
        # Weekend vs weekday
        if context.get('is_weekend'):
            preferences['genres'].extend(['семейный', 'комедия'])
            preferences['energy_level'] = 'high'
        
        return preferences