from textblob import TextBlob
import re
import logging

logger = logging.getLogger(__name__)

class MoodDetector:
    """Detects mood and sentiment from user text input"""
    
    # Russian mood keywords mapping
    MOOD_KEYWORDS = {
        'happy': ['�����', '���', '��������', '�������', '�����', '�����', '�����'],
        'sad': ['�����', '������', '����', '����', '�������', '������'],
        'excited': ['�������', '�����', '�������', '������', '�����'],
        'relaxed': ['������', '��������', '���', '�������', '�����'],
        'romantic': ['��������', '�����', '����', '������'],
        'thoughtful': ['��������', '��������', '�������', '������'],
        'scared': ['������', '������', '����', '�����'],
        'energetic': ['��������', '������', '����', '�����']
    }
    
    def detect_mood(self, text):
        """Detect mood from text"""
        text_lower = text.lower()
        
        # Check for explicit mood keywords
        mood_scores = {}
        for mood, keywords in self.MOOD_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                mood_scores[mood] = score
        
        if mood_scores:
            detected_mood = max(mood_scores, key=mood_scores.get)
            confidence = mood_scores[detected_mood] / sum(mood_scores.values())
        else:
            # Fallback to sentiment analysis
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.3:
                    detected_mood = 'happy'
                    confidence = min(polarity, 0.8)
                elif polarity < -0.3:
                    detected_mood = 'sad'
                    confidence = min(abs(polarity), 0.8)
                else:
                    detected_mood = 'neutral'
                    confidence = 0.5
            except:
                detected_mood = 'neutral'
                confidence = 0.5
        
        return {
            'mood': detected_mood,
            'confidence': confidence,
            'all_moods': mood_scores
        }