import os
from datetime import timedelta
from dotenv import load_dotenv


class Config:
    """Base configuration"""
    load_dotenv()
    SECRET_KEY = os.getenv('SECRET_KEY', 'okko-secret-key-change-in-production')
    APP_URL = os.getenv('APP_URL', 'http://localhost:3000')
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
    OPENROUTER_MODEL = 'anthropic/claude-3-sonnet'  # or 'openai/gpt-4'
    
    # Database Configuration (from okko_db.json)
    DB_HOST = os.getenv('DB_HOST', '109.73.203.167')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'default_db')
    DB_USER = os.getenv('DB_USER', 'vibethon')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'wCjP24a7&*N8')
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Embedding Model
    EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
    
    # CORS Configuration
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:5000']
    
    # Context Weights (for scoring algorithm)
    CONTEXT_WEIGHTS = {
        'mood': 0.3,
        'time_of_day': 0.15,
        'day_of_week': 0.1,
        'social_context': 0.15,
        'duration': 0.15
    }
    
    # Mood-Genre Mapping
    MOOD_GENRE_MAP = {
        'happy': ['комедия', 'приключения', 'семейный'],
        'sad': ['драма', 'мелодрама'],
        'excited': ['боевик', 'триллер', 'приключения'],
        'relaxed': ['комедия', 'семейный', 'документальный'],
        'romantic': ['мелодрама', 'комедия'],
        'thoughtful': ['драма', 'детектив', 'документальный'],
        'scared': ['ужасы', 'триллер'],
        'energetic': ['боевик', 'приключения', 'спорт']
    }
    
    # Time of Day Preferences
    TIME_PREFERENCES = {
        'morning': ['мотивационный', 'комедия', 'семейный'],
        'afternoon': ['боевик', 'приключения', 'документальный'],
        'evening': ['драма', 'триллер', 'детектив'],
        'night': ['ужасы', 'триллер', 'фантастика']
    }
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}