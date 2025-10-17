from flask import Flask, request, jsonify, Response, session
from flask_cors import CORS
import logging
import json
from datetime import datetime

from config import config
from services.llm_service import LLMService
from services.recommendation_engine import RecommendationEngine
from services.context_service import ContextService
from utils.prompts import PromptTemplates
from utils.mood_detector import MoodDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

# Initialize services
llm_service = LLMService(app.config)
recommendation_engine = RecommendationEngine(app.config)
context_service = ContextService(app.config)
mood_detector = MoodDetector()

# Store conversation history
conversation_history = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/context', methods=['POST'])
def get_context():
    """Get current context (time, weather, etc.)"""
    try:
        data = request.json
        city = data.get('city', 'Moscow')
        
        time_context = context_service.get_time_context()
        return jsonify({
            'success': True,
            'context': {
                **time_context
            }
        })
    except Exception as e:
        logger.error(f"Context error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        city = data.get('city', 'Moscow')
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Initialize or get conversation history
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Get context
        time_context = context_service.get_time_context()
        full_context = {**time_context}
        
        # Detect mood
        mood_info = mood_detector.detect_mood(user_message)
        
        # Build messages for LLM
        messages = [
            {'role': 'system', 'content': PromptTemplates.SYSTEM_PROMPT}
        ]
        
        # Add conversation history
        messages.extend(conversation_history[session_id][-10:])  # Last 10 messages
        
        # Add current user message with context
        context_prompt = PromptTemplates.create_recommendation_prompt(
            user_message, full_context, mood_info
        )
        messages.append({'role': 'user', 'content': context_prompt})
        
        # Get LLM response
        assistant_response = llm_service.create_chat_completion(
            messages, 
            stream=False, 
            temperature=0.7
        )
        
        # Update conversation history
        conversation_history[session_id].append({'role': 'user', 'content': user_message})
        conversation_history[session_id].append({'role': 'assistant', 'content': assistant_response})
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(
            user_message, 
            full_context, 
            limit=5
        )
        
        return jsonify({
            'success': True,
            'response': assistant_response,
            'recommendations': [
                {
                    'title': rec['movie']['serial_name'],
                    'description': rec['movie']['description'],
                    'genres': rec['movie'].get('genres', []),
                    'url': rec['movie']['url'],
                    'score': round(rec['score'], 2),
                    'mood_match': round(rec['mood_match'], 2),
                    'time_match': round(rec['time_match'], 2)
                }
                for rec in recommendations
            ],
            'context': full_context,
            'detected_mood': mood_info['mood']
        })
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Initialize conversation history
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Build messages
        messages = [
            {'role': 'system', 'content': PromptTemplates.SYSTEM_PROMPT}
        ]
        messages.extend(conversation_history[session_id][-10:])
        messages.append({'role': 'user', 'content': user_message})
        
        # Stream response
        def generate():
            full_response = ""
            for chunk in llm_service.create_chat_completion(messages, stream=True):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # Update history
            conversation_history[session_id].append({'role': 'user', 'content': user_message})
            conversation_history[session_id].append({'role': 'assistant', 'content': full_response})
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        logger.error(f"Stream error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get recommendations without chat"""
    try:
        data = request.json
        query = data.get('query', '')
        city = data.get('city', 'Moscow')
        
        # Get context
        time_context = context_service.get_time_context()
        full_context = {**time_context}
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(
            query, 
            full_context,
            limit=10
        )
        
        return jsonify({
            'success': True,
            'recommendations': [
                {
                    'title': rec['movie']['serial_name'],
                    'description': rec['movie']['description'],
                    'genres': rec['movie'].get('genres', []),
                    'url': rec['movie']['url'],
                    'score': round(rec['score'], 2)
                }
                for rec in recommendations
            ]
        })
    
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)