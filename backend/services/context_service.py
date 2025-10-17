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
        if isinstance(self.config, dict):
            self.time_preferences = self.config.get('TIME_PREFERENCES', {})
        else:
            self.time_preferences = self.config.TIME_PREFERENCES
    
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
    
    def determine_content_preferences(self, context):
        """Determine content preferences based on context"""
        preferences = {
            'genres': [],
            'mood': 'neutral',
            'energy_level': 'medium'
        }
        
        # Time-based preferences
        time_of_day = context.get('time_of_day')
        if time_of_day in self.time_preferences:
            preferences['genres'].extend(self.time_preferences[time_of_day])
        
        # Weekend vs weekday
        if context.get('is_weekend'):
            preferences['genres'].extend(['семейный', 'комедия'])
            preferences['energy_level'] = 'high'
        
        return preferences