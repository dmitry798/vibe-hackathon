import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database connections and queries"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.connection_params = {
            'host': self.config.DB_HOST,
            'port': self.config.DB_PORT,
            'database': self.config.DB_NAME,
            'user': self.config.DB_USER,
            'password': self.config.DB_PASSWORD
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def search_by_genres(self, genres, limit=20):
        """Search movies by genres"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT DISTINCT t.title_id, t.serial_name, t.content_type, 
                           t.age_rating, t.release_date, t.description, t.url,
                           array_agg(DISTINCT g.name) as genres,
                           array_agg(DISTINCT c.country) as countries,
                           array_agg(DISTINCT a.name) as actors,
                           d.name as director
                    FROM title t
                    LEFT JOIN title_genre tg ON t.title_id = tg.title_id
                    LEFT JOIN genre g ON tg.genre_id = g.genre_id
                    LEFT JOIN title_country c ON t.title_id = c.title_id
                    LEFT JOIN title_actor ta ON t.title_id = ta.title_id
                    LEFT JOIN actor a ON ta.actor_id = a.actor_id
                    LEFT JOIN title_director_item tdi ON t.title_id = tdi.title_id
                    LEFT JOIN director_item d ON tdi.director_item_id = d.director_item_id
                    WHERE g.name = ANY(%s)
                    GROUP BY t.title_id, t.serial_name, t.content_type, 
                             t.age_rating, t.release_date, t.description, t.url, d.name
                    ORDER BY t.release_date DESC
                    LIMIT %s
                """
                cur.execute(query, (genres, limit))
                return cur.fetchall()
    
    def search_by_title(self, title_query):
        """Search movies by title (fuzzy match)"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT DISTINCT t.title_id, t.serial_name, t.content_type,
                           t.description, t.url,
                           array_agg(DISTINCT g.name) as genres
                    FROM title t
                    LEFT JOIN title_genre tg ON t.title_id = tg.title_id
                    LEFT JOIN genre g ON tg.genre_id = g.genre_id
                    WHERE t.serial_name ILIKE %s
                    GROUP BY t.title_id, t.serial_name, t.content_type, t.description, t.url
                    LIMIT 10
                """
                cur.execute(query, (f'%{title_query}%',))
                return cur.fetchall()
    
    def get_similar_to_title(self, title_id, limit=10):
        """Get similar movies based on shared genres and actors"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    WITH target_movie AS (
                        SELECT t.title_id, 
                               array_agg(DISTINCT tg.genre_id) as genres,
                               array_agg(DISTINCT ta.actor_id) as actors
                        FROM title t
                        LEFT JOIN title_genre tg ON t.title_id = tg.title_id
                        LEFT JOIN title_actor ta ON t.title_id = ta.title_id
                        WHERE t.title_id = %s
                        GROUP BY t.title_id
                    )
                    SELECT t.title_id, t.serial_name, t.description, t.url,
                           array_agg(DISTINCT g.name) as genres,
                           COUNT(DISTINCT CASE WHEN tg.genre_id = ANY(tm.genres) THEN tg.genre_id END) as genre_match,
                           COUNT(DISTINCT CASE WHEN ta.actor_id = ANY(tm.actors) THEN ta.actor_id END) as actor_match
                    FROM title t, target_movie tm
                    LEFT JOIN title_genre tg ON t.title_id = tg.title_id
                    LEFT JOIN genre g ON tg.genre_id = g.genre_id
                    LEFT JOIN title_actor ta ON t.title_id = ta.title_id
                    WHERE t.title_id != %s
                      AND (tg.genre_id = ANY(tm.genres) OR ta.actor_id = ANY(tm.actors))
                    GROUP BY t.title_id, t.serial_name, t.description, t.url
                    ORDER BY genre_match DESC, actor_match DESC
                    LIMIT %s
                """
                cur.execute(query, (title_id, title_id, limit))
                return cur.fetchall()
    
    def get_by_filters(self, filters):
        """Advanced filtering: genres, country, year range, age rating"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                conditions = []
                params = []
                
                if filters.get('genres'):
                    conditions.append("g.name = ANY(%s)")
                    params.append(filters['genres'])
                
                if filters.get('country'):
                    conditions.append("c.country = %s")
                    params.append(filters['country'])
                
                if filters.get('year_from'):
                    conditions.append("EXTRACT(YEAR FROM t.release_date) >= %s")
                    params.append(filters['year_from'])
                
                if filters.get('year_to'):
                    conditions.append("EXTRACT(YEAR FROM t.release_date) <= %s")
                    params.append(filters['year_to'])
                
                if filters.get('max_age_rating'):
                    conditions.append("t.age_rating <= %s")
                    params.append(filters['max_age_rating'])
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                query = f"""
                    SELECT DISTINCT t.title_id, t.serial_name, t.content_type,
                           t.age_rating, t.release_date, t.description, t.url,
                           array_agg(DISTINCT g.name) as genres
                    FROM title t
                    LEFT JOIN title_genre tg ON t.title_id = tg.title_id
                    LEFT JOIN genre g ON tg.genre_id = g.genre_id
                    LEFT JOIN title_country c ON t.title_id = c.title_id
                    WHERE {where_clause}
                    GROUP BY t.title_id, t.serial_name, t.content_type,
                             t.age_rating, t.release_date, t.description, t.url
                    ORDER BY t.release_date DESC
                    LIMIT 20
                """
                cur.execute(query, params)
                return cur.fetchall()