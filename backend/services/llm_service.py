import requests
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

class LLMService:
    """Handles communication with OpenRouter API"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.api_key = self.config.OPENROUTER_API_KEY
        self.base_url = self.config.OPENROUTER_BASE_URL
        self.model = self.config.OPENROUTER_MODEL
        
    def create_chat_completion(self, messages, stream=False, temperature=0.7, max_tokens=1000):
        """Create chat completion with OpenRouter API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': self.config.APP_URL,
            'X-Title': 'Okko AI Assistant'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream
        }
        
        try:
            if stream:
                return self._stream_completion(headers, payload)
            else:
                response = requests.post(
                    f'{self.base_url}/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise
    
    def _stream_completion(self, headers, payload):
        """Stream completion responses"""
        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue