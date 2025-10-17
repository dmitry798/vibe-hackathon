import logging
from models.database import DatabaseManager
from models.embeddings import EmbeddingManager
from services.context_service import ContextService
from utils.mood_detector import MoodDetector
from config import Config

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Advanced recommendation engine with contextual awareness"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.db = DatabaseManager(config)
        self.embeddings = EmbeddingManager()
        self.context_service = ContextService(config)
        self.mood_detector = MoodDetector()
    
    def generate_recommendations(self, user_query, context=None, limit=10):
        """Generate contextual recommendations"""
        # Detect mood from query
        mood_info = self.mood_detector.detect_mood(user_query)
        detected_mood = mood_info['mood']
        
        # Get current context if not provided
        if not context:
            time_context = self.context_service.get_time_context()
            context = {**time_context}
        
        # Determine genre preferences
        genre_preferences = self._determine_genres(detected_mood, context)
        
        # Search database
        movies = self.db.search_by_genres(genre_preferences, limit=limit*2)
        
        # Score and rank
        scored_movies = self._score_movies(movies, detected_mood, context)
        
        # Return top recommendations
        return scored_movies[:limit]
    
    def _determine_genres(self, mood, context):
        """Determine preferred genres based on mood and context"""
        genres = set()
        
        # Mood-based genres
        if mood in self.config.MOOD_GENRE_MAP:
            genres.update(self.config.MOOD_GENRE_MAP[mood])
        
        # Context-based genres
        content_prefs = self.context_service.determine_content_preferences(context)
        genres.update(content_prefs['genres'])
        
        return list(genres)
    
    def _score_movies(self, movies, mood, context):
        """Score movies based on multiple factors"""
        scored = []
        
        for movie in movies:
            score = 0.0
            
            # Mood match score
            mood_score = self._calculate_mood_score(movie, mood)
            score += mood_score * self.config.CONTEXT_WEIGHTS['mood']
            
            # Time of day score
            time_score = self._calculate_time_score(movie, context.get('time_of_day'))
            score += time_score * self.config.CONTEXT_WEIGHTS['time_of_day']
            
            # Recency score
            recency_score = self._calculate_recency_score(movie)
            score += recency_score * 0.1
            
            scored.append({
                'movie': movie,
                'score': score,
                'mood_match': mood_score,
                'time_match': time_score,
            })
        
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored
    
    def _calculate_mood_score(self, movie, mood):
        """Calculate mood compatibility score"""
        if mood not in self.config.MOOD_GENRE_MAP:
            return 0.5
        
        preferred_genres = set(self.config.MOOD_GENRE_MAP[mood])
        movie_genres = set(movie.get('genres', []))
        
        if not movie_genres:
            return 0.3
        
        intersection = preferred_genres & movie_genres
        return len(intersection) / len(preferred_genres) if preferred_genres else 0.5
    
    def _calculate_time_score(self, movie, time_of_day):
        """Calculate time of day compatibility"""
        if not time_of_day or time_of_day not in self.config.TIME_PREFERENCES:
            return 0.5
        
        preferred_genres = set(self.config.TIME_PREFERENCES[time_of_day])
        movie_genres = set(movie.get('genres', []))
        
        intersection = preferred_genres & movie_genres
        return len(intersection) / len(preferred_genres) if preferred_genres else 0.3
    
    def _calculate_recency_score(self, movie):
        """Score based on release date (prefer recent but not only new)"""
        from datetime import datetime
        
        release_date = movie.get('release_date')
        if not release_date:
            return 0.5
        
        if isinstance(release_date, str):
            release_date = datetime.fromisoformat(release_date.split('T')[0])
        
        years_old = (datetime.now() - release_date).days / 365.25
        
        # Sigmoid-like scoring: peak around 2-5 years old
        if years_old < 1:
            return 0.9
        elif years_old < 5:
            return 1.0
        elif years_old < 10:
            return 0.7
        else:
            return 0.5