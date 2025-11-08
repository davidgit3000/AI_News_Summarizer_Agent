"""
Integrated ingestion pipeline that fetches news and stores in database.
Combines NewsFetcher and DatabaseManager for end-to-end data ingestion.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from src.ingestion.news_fetcher import NewsFetcher
from src.database.db_manager import DatabaseManager
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """End-to-end pipeline for fetching and storing news articles."""
    
    def __init__(
        self,
        news_api_key: Optional[str] = None,
        db_path: Optional[str] = None
    ):
        """
        Initialize the ingestion pipeline.
        
        Args:
            news_api_key: NewsAPI key (optional, uses config if not provided)
            db_path: Database path (optional, uses config if not provided)
        """
        self.fetcher = NewsFetcher(api_key=news_api_key)
        self.db = DatabaseManager(db_path=db_path)
        self.settings = get_settings()
        
        logger.info("IngestionPipeline initialized successfully")
    
    def ingest_top_headlines(
        self,
        query: Optional[str] = None,
        sources: Optional[str] = None,
        category: Optional[str] = None,
        page_size: int = 20
    ) -> Dict[str, int]:
        """
        Fetch top headlines and store in database.
        
        Args:
            query: Search query
            sources: News sources
            category: News category
            page_size: Number of articles to fetch
        
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Starting top headlines ingestion...")
        
        try:
            # Fetch articles
            articles = self.fetcher.fetch_top_headlines(
                query=query,
                sources=sources,
                category=category,
                page_size=page_size
            )
            
            # Store in database
            inserted, duplicates = self.db.insert_articles_batch(articles)
            
            stats = {
                'fetched': len(articles),
                'inserted': inserted,
                'duplicates': duplicates,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Ingestion complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            raise
    
    def ingest_by_topic(
        self,
        topic: str,
        days_back: int = 7,
        max_results: int = 20
    ) -> Dict[str, int]:
        """
        Fetch articles about a specific topic and store in database.
        
        Args:
            topic: Topic to search for
            days_back: How many days back to search
            max_results: Maximum number of articles
        
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting topic ingestion for: {topic}")
        
        try:
            # Fetch articles
            articles = self.fetcher.fetch_by_topic(
                topic=topic,
                days_back=days_back,
                max_results=max_results
            )
            
            # Store in database
            inserted, duplicates = self.db.insert_articles_batch(articles)
            
            stats = {
                'topic': topic,
                'fetched': len(articles),
                'inserted': inserted,
                'duplicates': duplicates,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Topic ingestion complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during topic ingestion: {e}")
            raise
    
    def ingest_everything(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sources: Optional[str] = None,
        sort_by: str = 'publishedAt',
        page_size: int = 50
    ) -> Dict[str, int]:
        """
        Search and ingest articles with advanced filters.
        
        Args:
            query: Search query (required)
            from_date: Start date
            to_date: End date
            sources: News sources
            sort_by: Sort order
            page_size: Number of articles
        
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting advanced search ingestion for: {query}")
        
        try:
            # Fetch articles
            articles = self.fetcher.fetch_everything(
                query=query,
                from_date=from_date,
                to_date=to_date,
                sources=sources,
                sort_by=sort_by,
                page_size=page_size
            )
            
            # Store in database
            inserted, duplicates = self.db.insert_articles_batch(articles)
            
            stats = {
                'query': query,
                'fetched': len(articles),
                'inserted': inserted,
                'duplicates': duplicates,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Advanced ingestion complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during advanced ingestion: {e}")
            raise
    
    def refresh_database(
        self,
        topics: Optional[List[str]] = None,
        days_back: int = 7,
        articles_per_topic: int = 10
    ) -> Dict[str, Any]:
        """
        Refresh the database with latest articles on multiple topics.
        
        Args:
            topics: List of topics to fetch (uses default if None)
            days_back: How many days back to search
            articles_per_topic: Articles to fetch per topic
        
        Returns:
            Dictionary with overall statistics
        """
        # Default topics if none provided
        if not topics:
            topics = [
                'artificial intelligence',
                'technology',
                'science',
                'business',
                'health'
            ]
        
        logger.info(f"Refreshing database with {len(topics)} topics...")
        
        overall_stats = {
            'topics_processed': 0,
            'total_fetched': 0,
            'total_inserted': 0,
            'total_duplicates': 0,
            'topic_stats': []
        }
        
        for topic in topics:
            try:
                stats = self.ingest_by_topic(
                    topic=topic,
                    days_back=days_back,
                    max_results=articles_per_topic
                )
                
                overall_stats['topics_processed'] += 1
                overall_stats['total_fetched'] += stats['fetched']
                overall_stats['total_inserted'] += stats['inserted']
                overall_stats['total_duplicates'] += stats['duplicates']
                overall_stats['topic_stats'].append(stats)
                
            except Exception as e:
                logger.error(f"Error processing topic '{topic}': {e}")
                continue
        
        # Get final database stats
        overall_stats['database_stats'] = self.db.get_stats()
        overall_stats['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Database refresh complete: {overall_stats}")
        return overall_stats
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current pipeline and database status.
        
        Returns:
            Dictionary with status information
        """
        db_stats = self.db.get_stats()
        
        status = {
            'database_path': self.db.db_path,
            'total_articles': db_stats['total_articles'],
            'articles_with_embeddings': db_stats['articles_with_embeddings'],
            'articles_without_embeddings': db_stats['articles_without_embeddings'],
            'sources': db_stats['articles_by_source'],
            'timestamp': datetime.now().isoformat()
        }
        
        return status


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("AI News Summarizer - Ingestion Pipeline Test")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        print("\n[1/4] Initializing pipeline...")
        pipeline = IngestionPipeline()
        print("✅ Pipeline initialized")
        
        # Check initial status
        print("\n[2/4] Checking initial database status...")
        status = pipeline.get_pipeline_status()
        print(f"   Total articles: {status['total_articles']}")
        
        # Ingest some articles
        print("\n[3/4] Ingesting articles...")
        print("   Fetching top headlines...")
        stats = pipeline.ingest_top_headlines(page_size=5)
        print(f"   ✅ Fetched: {stats['fetched']}, Inserted: {stats['inserted']}, Duplicates: {stats['duplicates']}")
        
        # Show final status
        print("\n[4/4] Final database status...")
        final_status = pipeline.get_pipeline_status()
        print(f"   Total articles: {final_status['total_articles']}")
        print(f"   Articles by source:")
        for source, count in final_status['sources'].items():
            print(f"      - {source}: {count}")
        
        print("\n" + "=" * 60)
        print("✅ Ingestion pipeline test completed successfully!")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file (copy from .env.example)")
        print("2. Added your NEWSAPI_KEY to the .env file")
        print("\nGet your API key at: https://newsapi.org/register")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
