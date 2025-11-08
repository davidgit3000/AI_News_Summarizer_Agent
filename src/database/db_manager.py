"""
Database manager for storing and retrieving news articles.
Uses SQLite for local caching with support for embeddings.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database for article storage and retrieval."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses config.
        """
        settings = get_settings()
        self.db_path = db_path or settings.database_path
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        logger.info(f"DatabaseManager initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT,
                    author TEXT,
                    published_at TEXT,
                    url_to_image TEXT,
                    fetched_at TEXT NOT NULL,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on URL for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_url ON articles(url)
            """)
            
            # Create index on source
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON articles(source)
            """)
            
            # Create index on published_at
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_published_at ON articles(published_at)
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully")
    
    def insert_article(self, article: Dict[str, Any]) -> Optional[int]:
        """
        Insert a single article into the database.
        
        Args:
            article: Article dictionary with keys: title, description, content, url, etc.
        
        Returns:
            Article ID if inserted, None if duplicate
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO articles (
                        title, description, content, url, source, author,
                        published_at, url_to_image, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.get('title', ''),
                    article.get('description', ''),
                    article.get('content', ''),
                    article['url'],  # Required field
                    article.get('source', 'Unknown'),
                    article.get('author', 'Unknown'),
                    article.get('published_at', ''),
                    article.get('url_to_image', ''),
                    article.get('fetched_at', datetime.now().isoformat())
                ))
                
                conn.commit()
                article_id = cursor.lastrowid
                logger.debug(f"Inserted article: {article.get('title', 'Untitled')} (ID: {article_id})")
                return article_id
                
        except sqlite3.IntegrityError:
            logger.debug(f"Article already exists: {article.get('url', 'Unknown URL')}")
            return None
        except Exception as e:
            logger.error(f"Error inserting article: {e}")
            raise
    
    def insert_articles_batch(self, articles: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Insert multiple articles in a batch.
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Tuple of (inserted_count, duplicate_count)
        """
        inserted = 0
        duplicates = 0
        
        for article in articles:
            result = self.insert_article(article)
            if result is not None:
                inserted += 1
            else:
                duplicates += 1
        
        logger.info(f"Batch insert complete: {inserted} new, {duplicates} duplicates")
        return inserted, duplicates
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an article by its ID.
        
        Args:
            article_id: Article ID
        
        Returns:
            Article dictionary or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an article by its URL.
        
        Args:
            url: Article URL
        
        Returns:
            Article dictionary or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM articles WHERE url = ?", (url,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_all_articles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all articles from the database.
        
        Args:
            limit: Maximum number of articles to return
        
        Returns:
            List of article dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM articles ORDER BY published_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_articles_by_source(self, source: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve articles from a specific source.
        
        Args:
            source: Source name
            limit: Maximum number of articles
        
        Returns:
            List of article dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM articles WHERE source = ? ORDER BY published_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (source,))
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def search_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search articles by keyword in title or content using word boundaries.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of matching article dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Use word boundaries for better matching
            # Match whole words or at word boundaries (space, punctuation)
            words = query.lower().split()
            
            if len(words) == 1:
                # For single word, use word boundary patterns
                word = words[0]
                # Match: start of string, after space, or after punctuation
                patterns = [
                    f"% {word} %",  # word surrounded by spaces
                    f"{word} %",    # word at start
                    f"% {word}",    # word at end
                    f"{word}",      # exact match
                ]
                
                conditions = []
                params = []
                for pattern in patterns:
                    conditions.append("(LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(description) LIKE ?)")
                    params.extend([pattern, pattern, pattern])
                
                where_clause = " OR ".join(conditions)
                params.append(limit)
                
                cursor.execute(f"""
                    SELECT * FROM articles 
                    WHERE {where_clause}
                    ORDER BY published_at DESC
                    LIMIT ?
                """, params)
            else:
                # For multiple words, search for the phrase
                search_pattern = f"%{query}%"
                cursor.execute("""
                    SELECT * FROM articles 
                    WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(description) LIKE ?
                    ORDER BY published_at DESC
                    LIMIT ?
                """, (search_pattern.lower(), search_pattern.lower(), search_pattern.lower(), limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_embedding(self, article_id: int, embedding: np.ndarray) -> bool:
        """
        Update the embedding for an article.
        
        Args:
            article_id: Article ID
            embedding: Numpy array of embeddings
        
        Returns:
            True if successful
        """
        try:
            # Convert numpy array to bytes
            embedding_bytes = embedding.tobytes()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE articles SET embedding = ? WHERE id = ?",
                    (embedding_bytes, article_id)
                )
                conn.commit()
                
                logger.debug(f"Updated embedding for article ID: {article_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating embedding: {e}")
            return False
    
    def get_articles_without_embeddings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get articles that don't have embeddings yet.
        
        Args:
            limit: Maximum number of articles
        
        Returns:
            List of article dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM articles WHERE embedding IS NULL"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def delete_article(self, article_id: int) -> bool:
        """
        Delete an article by ID.
        
        Args:
            article_id: Article ID
        
        Returns:
            True if deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted article ID: {article_id}")
            return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with stats
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            
            # Articles with embeddings
            cursor.execute("SELECT COUNT(*) FROM articles WHERE embedding IS NOT NULL")
            with_embeddings = cursor.fetchone()[0]
            
            # Articles by source
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM articles 
                GROUP BY source 
                ORDER BY count DESC
            """)
            by_source = dict(cursor.fetchall())
            
            return {
                'total_articles': total,
                'articles_with_embeddings': with_embeddings,
                'articles_without_embeddings': total - with_embeddings,
                'articles_by_source': by_source
            }
    
    def clear_all_articles(self) -> int:
        """
        Delete all articles from the database.
        
        Returns:
            Number of articles deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles")
            conn.commit()
            
            deleted = cursor.rowcount
            logger.warning(f"Cleared all articles from database: {deleted} deleted")
            return deleted


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = DatabaseManager()
    
    # Test article
    test_article = {
        'title': 'Test Article',
        'description': 'This is a test article',
        'content': 'Full content of the test article...',
        'url': 'https://example.com/test-article',
        'source': 'Test Source',
        'author': 'Test Author',
        'published_at': datetime.now().isoformat(),
        'fetched_at': datetime.now().isoformat()
    }
    
    # Insert article
    print("\n=== Inserting Test Article ===")
    article_id = db.insert_article(test_article)
    print(f"Inserted article with ID: {article_id}")
    
    # Get stats
    print("\n=== Database Statistics ===")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Retrieve article
    print("\n=== Retrieving Article ===")
    retrieved = db.get_article_by_id(article_id) if article_id else None
    if retrieved:
        print(f"Title: {retrieved['title']}")
        print(f"Source: {retrieved['source']}")
