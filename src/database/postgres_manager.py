"""
PostgreSQL database manager using SQLAlchemy.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, LargeBinary, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

Base = declarative_base()


class Article(Base):
    """Article model for PostgreSQL."""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content = Column(Text)
    url = Column(String(1000), unique=True, nullable=False)
    source = Column(String(200))
    author = Column(String(200))
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    embedding = Column(LargeBinary)  # Store as bytes
    embedding_model = Column(String(100))


class PostgresManager:
    """PostgreSQL database manager."""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize PostgreSQL connection.
        
        Args:
            database_url: PostgreSQL connection string (from Neon)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Create engine with connection pooling for better performance
        self.engine = create_engine(
            self.database_url,
            pool_size=5,  # Keep 5 connections ready
            max_overflow=10,  # Allow up to 10 additional connections
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,
            connect_args={
                "connect_timeout": 10,  # 10 second timeout
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        logger.info(f"PostgresManager initialized with Neon database")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def insert_articles_batch(self, articles: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Insert multiple articles, skip duplicates.
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Tuple of (inserted_count, duplicate_count)
        """
        session = self.get_session()
        inserted = 0
        duplicates = 0
        
        try:
            for article_data in articles:
                # Check if article exists
                existing = session.query(Article).filter_by(url=article_data['url']).first()
                
                if existing:
                    duplicates += 1
                    continue
                
                # Create new article
                article = Article(
                    title=article_data.get('title', ''),
                    description=article_data.get('description'),
                    content=article_data.get('content'),
                    url=article_data['url'],
                    source=article_data.get('source'),
                    author=article_data.get('author'),
                    published_at=article_data.get('published_at')
                )
                
                session.add(article)
                inserted += 1
            
            session.commit()
            logger.info(f"Inserted {inserted} articles, {duplicates} duplicates")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting articles: {e}")
            raise
        finally:
            session.close()
        
        return inserted, duplicates
    
    def get_articles_without_embeddings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get articles that don't have embeddings yet."""
        session = self.get_session()
        
        try:
            query = session.query(Article).filter(Article.embedding.is_(None))
            
            if limit:
                query = query.limit(limit)
            
            articles = query.all()
            
            return [
                {
                    'id': a.id,
                    'title': a.title,
                    'description': a.description,
                    'content': a.content,
                    'url': a.url,
                    'source': a.source,
                    'author': a.author,
                    'published_at': a.published_at.isoformat() if a.published_at else None
                }
                for a in articles
            ]
        finally:
            session.close()
    
    def update_embedding(self, article_id: int, embedding: np.ndarray, model: str) -> bool:
        """Update article with embedding."""
        session = self.get_session()
        
        try:
            article = session.query(Article).filter_by(id=article_id).first()
            
            if not article:
                return False
            
            # Convert numpy array to bytes
            article.embedding = embedding.tobytes()
            article.embedding_model = model
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating embedding: {e}")
            return False
        finally:
            session.close()
    
    def search_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search articles by keyword."""
        session = self.get_session()
        
        try:
            # PostgreSQL full-text search
            articles = session.query(Article).filter(
                (Article.title.ilike(f'%{query}%')) |
                (Article.content.ilike(f'%{query}%')) |
                (Article.description.ilike(f'%{query}%'))
            ).order_by(Article.published_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': a.id,
                    'title': a.title,
                    'description': a.description,
                    'content': a.content,
                    'url': a.url,
                    'source': a.source,
                    'author': a.author,
                    'published_at': a.published_at.isoformat() if a.published_at else None
                }
                for a in articles
            ]
        finally:
            session.close()
    
    def get_articles_by_source(self, source: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get articles from a specific source."""
        session = self.get_session()
        
        try:
            query = session.query(Article).filter_by(source=source).order_by(Article.published_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            articles = query.all()
            
            return [
                {
                    'id': a.id,
                    'title': a.title,
                    'description': a.description,
                    'content': a.content,
                    'url': a.url,
                    'source': a.source,
                    'author': a.author,
                    'published_at': a.published_at.isoformat() if a.published_at else None
                }
                for a in articles
            ]
        finally:
            session.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        session = self.get_session()
        
        try:
            total = session.query(Article).count()
            with_embeddings = session.query(Article).filter(Article.embedding.isnot(None)).count()
            
            # Get source distribution
            sources = session.query(Article.source).distinct().all()
            articles_by_source = {}
            
            for (source,) in sources:
                if source:
                    count = session.query(Article).filter_by(source=source).count()
                    articles_by_source[source] = count
            
            return {
                'total_articles': total,
                'articles_with_embeddings': with_embeddings,
                'articles_by_source': articles_by_source
            }
        finally:
            session.close()
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get a single article by ID."""
        session = self.get_session()
        
        try:
            article = session.query(Article).filter_by(id=article_id).first()
            
            if not article:
                return None
            
            return {
                'id': article.id,
                'title': article.title,
                'description': article.description,
                'content': article.content,
                'url': article.url,
                'source': article.source,
                'author': article.author,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'embedding': np.frombuffer(article.embedding, dtype=np.float32) if article.embedding else None
            }
        finally:
            session.close()
    
    def get_articles_with_embeddings(self) -> List[Dict[str, Any]]:
        """Get all articles that have embeddings."""
        session = self.get_session()
        
        try:
            articles = session.query(Article).filter(Article.embedding.isnot(None)).all()
            
            return [
                {
                    'id': a.id,
                    'title': a.title,
                    'description': a.description,
                    'content': a.content,
                    'url': a.url,
                    'source': a.source,
                    'author': a.author,
                    'published_at': a.published_at.isoformat() if a.published_at else None,
                    'embedding': a.embedding  # Keep as bytes for migration
                }
                for a in articles
            ]
        finally:
            session.close()
    
    def get_all_articles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all articles from database."""
        session = self.get_session()
        
        try:
            query = session.query(Article).order_by(Article.published_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            articles = query.all()
            
            return [
                {
                    'id': a.id,
                    'title': a.title,
                    'description': a.description,
                    'content': a.content,
                    'url': a.url,
                    'source': a.source,
                    'author': a.author,
                    'published_at': a.published_at.isoformat() if a.published_at else None,
                    'embedding': np.frombuffer(a.embedding, dtype=np.float32) if a.embedding else None
                }
                for a in articles
            ]
        finally:
            session.close()