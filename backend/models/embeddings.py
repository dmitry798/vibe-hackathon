from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import os
import logging

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manages text embeddings for semantic search"""
    
    def __init__(self, model_name='sentence-transformers/paraphrase-multilingual-mpnet-base-v2'):
        self.model = SentenceTransformer(model_name)
        self.embeddings_cache = {}
        self.cache_file = 'data/embeddings/cache.pkl'
    
    def encode_text(self, text):
        """Encode text to vector embedding"""
        if isinstance(text, list):
            return self.model.encode(text, convert_to_numpy=True)
        return self.model.encode([text], convert_to_numpy=True)[0]
    
    def compute_similarity(self, embedding1, embedding2):
        """Compute cosine similarity between two embeddings"""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        return dot_product / (norm1 * norm2)
    
    def find_most_similar(self, query_embedding, candidate_embeddings, top_k=10):
        """Find most similar embeddings"""
        similarities = [
            (idx, self.compute_similarity(query_embedding, emb))
            for idx, emb in enumerate(candidate_embeddings)
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def cache_embeddings(self, movie_id, embedding):
        """Cache embedding for a movie"""
        self.embeddings_cache[movie_id] = embedding
    
    def save_cache(self):
        """Save embeddings cache to disk"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.embeddings_cache, f)
        logger.info(f"Saved {len(self.embeddings_cache)} embeddings to cache")
    
    def load_cache(self):
        """Load embeddings cache from disk"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as f:
                self.embeddings_cache = pickle.load(f)
            logger.info(f"Loaded {len(self.embeddings_cache)} embeddings from cache")