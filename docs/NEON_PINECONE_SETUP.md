# 🗄️ Neon + Pinecone Setup Guide

Complete guide to migrate from SQLite + ChromaDB to Neon (PostgreSQL) + Pinecone for production deployment.

---

## 📋 Overview

**What we're doing:**
- **Database**: SQLite → Neon PostgreSQL (serverless, free tier)
- **Vector Store**: ChromaDB → Pinecone (managed, free tier)

**Benefits:**
- ✅ Persistent storage (survives restarts)
- ✅ Scalable (handles more data)
- ✅ Production-ready
- ✅ Free tiers available

---

## Part 1: Neon PostgreSQL Setup

### Step 1: Create Neon Account

1. Go to [neon.tech](https://neon.tech)
2. Sign up with GitHub (easiest)
3. Create a new project:
   - **Project name**: `ai-news-summarizer`
   - **Region**: Choose closest to you
   - **PostgreSQL version**: 16 (latest)

### Step 2: Get Connection String

1. In Neon dashboard, go to your project
2. Click **"Connection Details"**
3. Copy the connection string (looks like):
   ```
   postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Save this - you'll need it!

### Step 3: Install PostgreSQL Dependencies

Add to `requirements.txt`:
```bash
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
```

Install locally:
```bash
pip install psycopg2-binary sqlalchemy
```

### Step 4: Update Database Manager

Create a new file `src/database/postgres_manager.py`:

```python
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
        
        # Create engine
        self.engine = create_engine(
            self.database_url,
            poolclass=NullPool,  # Serverless-friendly
            echo=False
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
```

### Step 5: Update Config

Modify `config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Database Configuration
    database_url: str = ""  # Neon PostgreSQL URL
    use_postgres: bool = True  # Set to True to use PostgreSQL
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 6: Update .env

Add to your `.env` file:

```bash
# Neon PostgreSQL
DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
USE_POSTGRES=true
```

---

## Part 2: Pinecone Vector Database Setup

### Step 1: Create Pinecone Account

1. Go to [pinecone.io](https://pinecone.io)
2. Sign up (free tier: 1M vectors, 1 index)
3. Create an API key:
   - Go to **API Keys** in dashboard
   - Click **"Create API Key"**
   - Copy the key (starts with `pc-...`)

### Step 2: Create Index

1. In Pinecone dashboard, click **"Create Index"**
2. Settings:
   - **Name**: `news-articles`
   - **Dimensions**: `384` (for all-MiniLM-L6-v2 model)
   - **Metric**: `cosine`
   - **Cloud**: `AWS` (free tier)
   - **Region**: `us-east-1` (free tier)

### Step 3: Install Pinecone

Add to `requirements.txt`:
```bash
pinecone-client==3.0.0
```

Install locally:
```bash
pip install pinecone-client
```

### Step 4: Create Pinecone Vector Store

Create `src/retrieval/pinecone_store.py`:

```python
"""
Pinecone vector store implementation.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)


class PineconeStore:
    """Pinecone vector store for semantic search."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: str = "news-articles",
        dimension: int = 384
    ):
        """
        Initialize Pinecone connection.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.index_name = index_name
        self.dimension = dimension
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not set")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Create index if it doesn't exist
        if index_name not in self.pc.list_indexes().names():
            logger.info(f"Creating Pinecone index: {index_name}")
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
        # Connect to index
        self.index = self.pc.Index(index_name)
        
        logger.info(f"PineconeStore initialized: {index_name}")
        logger.info(f"Index stats: {self.index.describe_index_stats()}")
    
    def add_articles(
        self,
        articles: List[Dict[str, Any]],
        embeddings: List[np.ndarray]
    ) -> int:
        """
        Add articles with embeddings to Pinecone.
        
        Args:
            articles: List of article dictionaries
            embeddings: List of embedding vectors
        
        Returns:
            Number of articles added
        """
        if len(articles) != len(embeddings):
            raise ValueError("Number of articles must match number of embeddings")
        
        vectors = []
        
        for article, embedding in zip(articles, embeddings):
            # Prepare metadata (Pinecone has size limits)
            metadata = {
                'article_id': article['id'],
                'title': article.get('title', '')[:500],  # Limit size
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'published_at': article.get('published_at', ''),
            }
            
            # Add description if available (truncate to fit metadata limits)
            if article.get('description'):
                metadata['description'] = article['description'][:1000]
            
            vectors.append({
                'id': str(article['id']),
                'values': embedding.tolist(),
                'metadata': metadata
            })
        
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
        
        logger.info(f"Added {len(vectors)} articles to Pinecone")
        return len(vectors)
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        min_similarity: float = 0.0,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar articles.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            filter_dict: Metadata filters (e.g., {'source': 'BBC'})
        
        Returns:
            List of matching articles with metadata
        """
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        # Format results
        matches = []
        for match in results['matches']:
            similarity = match['score']
            
            if similarity < min_similarity:
                continue
            
            matches.append({
                'id': match['id'],
                'similarity': similarity,
                'metadata': match['metadata']
            })
        
        logger.info(f"Found {len(matches)} matches (min_similarity={min_similarity})")
        return matches
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """Delete vectors by IDs."""
        self.index.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} vectors from Pinecone")
    
    def get_collection_size(self) -> int:
        """Get number of vectors in index."""
        stats = self.index.describe_index_stats()
        return stats['total_vector_count']
    
    def clear_index(self) -> None:
        """Delete all vectors from index."""
        self.index.delete(delete_all=True)
        logger.info("Cleared all vectors from Pinecone index")
```

### Step 5: Update Retrieval Pipeline

Modify `src/retrieval/pipeline.py` to support Pinecone:

```python
from config import settings

class RetrievalPipeline:
    def __init__(self):
        # Choose vector store based on config
        if settings.vector_store_type == "pinecone":
            from src.retrieval.pinecone_store import PineconeStore
            self.vector_store = PineconeStore()
        else:
            from src.retrieval.vector_store import VectorStore
            self.vector_store = VectorStore()
        
        # ... rest of initialization ...
```

### Step 6: Update Config for Pinecone

Add to `config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Vector Store Configuration
    vector_store_type: str = "pinecone"  # "chromadb" or "pinecone"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "news-articles"
    
    class Config:
        env_file = ".env"
```

### Step 7: Update .env

Add to your `.env` file:

```bash
# Pinecone Vector Database
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=pc-xxxxxxxxxxxxxxxxxxxxx
PINECONE_INDEX_NAME=news-articles
```

---

## Part 3: Migration Script

Create `migrate_to_neon_pinecone.py`:

```python
"""
Migration script: SQLite + ChromaDB → Neon + Pinecone
"""

import logging
from src.database.db_manager import DatabaseManager as SQLiteManager
from src.database.postgres_manager import PostgresManager
from src.retrieval.vector_store import VectorStore as ChromaStore
from src.retrieval.pinecone_store import PineconeStore
from src.vectorization.embedder import TextEmbedder
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Migrate articles from SQLite to Neon PostgreSQL."""
    logger.info("Starting database migration...")
    
    # Connect to both databases
    sqlite_db = SQLiteManager()
    postgres_db = PostgresManager()
    
    # Get all articles from SQLite
    articles = sqlite_db.get_all_articles()
    logger.info(f"Found {len(articles)} articles in SQLite")
    
    # Insert into PostgreSQL
    inserted, duplicates = postgres_db.insert_articles_batch(articles)
    logger.info(f"Migrated {inserted} articles, {duplicates} duplicates")
    
    return inserted


def migrate_vectors():
    """Migrate vectors from ChromaDB to Pinecone."""
    logger.info("Starting vector migration...")
    
    # Connect to both stores
    chroma_store = ChromaStore()
    pinecone_store = PineconeStore()
    
    # Get PostgreSQL database
    postgres_db = PostgresManager()
    
    # Get all articles with embeddings
    articles = postgres_db.get_articles_with_embeddings()
    logger.info(f"Found {len(articles)} articles with embeddings")
    
    # Extract embeddings
    embeddings = [np.frombuffer(a['embedding'], dtype=np.float32) for a in articles]
    
    # Add to Pinecone
    count = pinecone_store.add_articles(articles, embeddings)
    logger.info(f"Migrated {count} vectors to Pinecone")
    
    return count


if __name__ == "__main__":
    print("🚀 Starting migration to Neon + Pinecone...")
    print()
    
    # Migrate database
    print("📊 Step 1: Migrating articles to Neon PostgreSQL...")
    article_count = migrate_database()
    print(f"✅ Migrated {article_count} articles")
    print()
    
    # Migrate vectors
    print("🔍 Step 2: Migrating vectors to Pinecone...")
    vector_count = migrate_vectors()
    print(f"✅ Migrated {vector_count} vectors")
    print()
    
    print("🎉 Migration complete!")
    print()
    print("Next steps:")
    print("1. Update your .env file with Neon and Pinecone credentials")
    print("2. Set USE_POSTGRES=true and VECTOR_STORE_TYPE=pinecone")
    print("3. Test the application locally")
    print("4. Deploy to your hosting platform")
```

---

## Part 4: Testing

### Test Neon Connection

```python
from src.database.postgres_manager import PostgresManager

db = PostgresManager()
stats = db.get_stats()
print(f"Total articles: {stats['total_articles']}")
print(f"With embeddings: {stats['articles_with_embeddings']}")
```

### Test Pinecone Connection

```python
from src.retrieval.pinecone_store import PineconeStore

store = PineconeStore()
size = store.get_collection_size()
print(f"Vectors in Pinecone: {size}")
```

---

## Part 5: Deployment

### Update .env for Production

```bash
# Neon PostgreSQL
DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
USE_POSTGRES=true

# Pinecone
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=pc-xxxxxxxxxxxxxxxxxxxxx
PINECONE_INDEX_NAME=news-articles

# API Keys
OPENAI_API_KEY=sk-...
NEWSAPI_KEY=...
GEMINI_API_KEY=...
```

### Deploy to Railway/Render

1. Add environment variables in platform dashboard
2. Push code to GitHub
3. Deploy!

**No persistent volumes needed** - everything is in managed services! 🎉

---

## 📊 Cost Breakdown

### Free Tier Limits

**Neon:**
- ✅ 0.5 GB storage
- ✅ 1 project
- ✅ 10 branches
- **Perfect for this app!**

**Pinecone:**
- ✅ 1M vectors (≈1M articles)
- ✅ 1 index
- ✅ 100 queries/second
- **More than enough!**

**Total Cost:** $0/month (free tiers)

---

## 🎯 Summary

**What you get:**
- ✅ Persistent PostgreSQL database (Neon)
- ✅ Scalable vector search (Pinecone)
- ✅ No local storage needed
- ✅ Production-ready
- ✅ Free tier available
- ✅ Easy deployment

**Next steps:**
1. Set up Neon account
2. Set up Pinecone account
3. Update code with new managers
4. Run migration script
5. Test locally
6. Deploy!

🚀 Your app is now production-ready!
