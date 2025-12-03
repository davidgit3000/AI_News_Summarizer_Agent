"""
News Agent Orchestrator - Intelligent pipeline automation.

This module handles the entire workflow automatically:
1. Parse user query to extract topic and intent
2. Check if relevant articles exist in vector store
3. Fetch new articles if needed
4. Generate summary with citations
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import re

from src.ingestion.pipeline import IngestionPipeline
from src.retrieval.pipeline import RetrievalPipeline
from src.summarization.pipeline import SummarizationPipeline

logger = logging.getLogger(__name__)


class NewsAgentOrchestrator:
    """
    Intelligent agent that orchestrates the full news summarization pipeline.
    
    The agent automatically:
    - Determines if new articles need to be fetched
    - Searches existing knowledge base
    - Generates summaries with citations
    - Manages caching and freshness
    """
    
    def __init__(self):
        """Initialize the orchestrator with all required pipelines."""
        self.ingestion = IngestionPipeline()
        self.retrieval = RetrievalPipeline()
        self.summarization = SummarizationPipeline()
        
        # Configuration
        self.min_articles = 5  # Minimum articles needed
        self.max_article_age_hours = 24  # Consider articles stale after 24 hours
        self.default_fetch_days = 7  # Default lookback period for fetching
        
        logger.info("NewsAgentOrchestrator initialized")
    
    def process_query(self, user_query: str, max_articles: int = 10, 
                     summary_length: int = 200, style: str = "concise") -> Dict[str, Any]:
        """
        Main entry point - processes user query end-to-end.
        
        Args:
            user_query: Natural language query from user
            max_articles: Maximum articles to use for summary
            summary_length: Target summary length in words
            style: Summary style (concise, comprehensive, etc.)
        
        Returns:
            Dictionary containing:
                - summary: Generated summary text
                - sources: List of source articles with metadata
                - articles_used: Number of articles used
                - newly_fetched: Number of new articles fetched
                - cached: Whether results came from cache
                - topic: Extracted topic
        """
        logger.info(f"Processing query: {user_query}")
        
        # Step 1: Extract topic from query
        topic = self._extract_topic(user_query)
        logger.info(f"Extracted topic: {topic}")
        
        # Step 2: Search existing articles
        existing_articles = self.retrieval.retrieve_for_query(
            query=topic,
            top_k=max_articles * 2  # Get more to filter by freshness
        )
        
        logger.info(f"Found {len(existing_articles)} existing articles in vector store")
        
        # Step 2.5: If no articles found in vector store, try syncing from database
        if not existing_articles:
            logger.info("No articles in vector store, checking database...")
            try:
                sync_stats = self.retrieval.sync_database_to_vector_store()
                synced_count = sync_stats.get('synced', 0)
                if synced_count > 0:
                    logger.info(f"Synced {synced_count} articles from database to vector store")
                    # Re-search after sync
                    existing_articles = self.retrieval.retrieve_for_query(
                        query=topic,
                        top_k=max_articles * 2
                    )
                    logger.info(f"Found {len(existing_articles)} articles after sync")
            except Exception as e:
                logger.error(f"Error syncing database to vector store: {e}")
        
        # Step 3: Determine if we need fresh data
        needs_refresh, reason = self._needs_refresh(existing_articles, topic)
        newly_fetched = 0
        
        if needs_refresh:
            logger.info(f"Fetching new articles: {reason}")
            try:
                # Fetch new articles
                stats = self.ingestion.ingest_everything(
                    query=topic,
                    from_date=datetime.now(timezone.utc) - timedelta(days=self.default_fetch_days),
                    to_date=datetime.now(timezone.utc),
                    page_size=20,
                    sort_by='relevancy'
                )
                newly_fetched = stats.get('inserted', 0)
                logger.info(f"Fetched {newly_fetched} new articles")
                
                # Generate embeddings and sync new articles to vector store
                if newly_fetched > 0:
                    logger.info("Generating embeddings for new articles...")
                    from src.vectorization.embedder import TextEmbedder
                    from src.database.db_factory import get_database_manager
                    
                    embedder = TextEmbedder()
                    db = get_database_manager()
                    
                    # Get articles without embeddings
                    all_articles = db.get_all_articles()
                    articles_without_embeddings = [a for a in all_articles if a.get('embedding') is None]
                    
                    # Generate embeddings for new articles
                    embedded_count = 0
                    for article in articles_without_embeddings[:newly_fetched]:  # Only process newly fetched
                        try:
                            text = f"{article.get('title', '')}. {article.get('content', '')}"[:5000]
                            if text.strip():
                                embedding = embedder.embed_text(text)
                                db.update_embedding(article['id'], embedding, embedder.model_name)
                                embedded_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to embed article {article['id']}: {e}")
                    
                    logger.info(f"Generated embeddings for {embedded_count} articles")
                    
                    # Now sync to Pinecone
                    logger.info("Syncing new articles to vector store...")
                    sync_stats = self.retrieval.sync_database_to_vector_store()
                    logger.info(f"Synced {sync_stats.get('synced', 0)} articles to vector store")
                    
                    # Re-search to get fresh results
                    existing_articles = self.retrieval.retrieve_for_query(
                        query=topic,
                        top_k=max_articles * 2
                    )
            except Exception as e:
                logger.error(f"Error fetching new articles: {e}")
                # Continue with existing articles if fetch fails
        
        # Step 4: Generate summary (summarization pipeline will retrieve articles)
        logger.info(f"Generating summary for topic: {topic}")
        try:
            result = self.summarization.summarize_topic(
                topic=topic,
                max_articles=max_articles,
                summary_length=summary_length,
                style=style
            )
            
            summary_text = result.get('summary', '')
            sources = result.get('sources', [])
            articles = result.get('articles', [])  # Get full articles with document content
            articles_used = result.get('article_count', 0)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                'summary': None,
                'sources': [],
                'articles': [],
                'articles_used': 0,
                'newly_fetched': newly_fetched,
                'cached': newly_fetched == 0,
                'topic': topic,
                'error': f'Error generating summary: {str(e)}'
            }
        
        # Check if summary was generated
        if not summary_text or summary_text == "No relevant articles found for this topic.":
            return {
                'summary': None,
                'sources': [],
                'articles': [],
                'articles_used': articles_used,
                'newly_fetched': newly_fetched,
                'cached': newly_fetched == 0,
                'topic': topic,
                'error': 'No relevant articles found for this topic. Try a different query or check back later.'
            }
        
        # Step 5: Format response
        return {
            'summary': summary_text,
            'sources': sources,
            'articles': articles,  # Include full articles for validation
            'articles_used': articles_used,
            'newly_fetched': newly_fetched,
            'cached': newly_fetched == 0,
            'topic': topic,
            'error': None
        }
    
    def _extract_topic(self, user_query: str) -> str:
        """
        Extract the main topic from user query.
        
        For now, uses simple heuristics. Can be enhanced with NLP later.
        
        Args:
            user_query: User's natural language query
        
        Returns:
            Extracted topic string
        """
        # Remove common question words and phrases
        query_lower = user_query.lower()
        
        # Patterns to remove
        patterns_to_remove = [
            r'^(tell me about|tell me something new about|what\'?s new with|what is|what are|explain|summarize|find|search for|get news about|news on|news about)\s+',
            r'^(can you|could you|please|i want to know about|give me)\s+',
            r'\?$',  # Remove trailing question mark
        ]
        
        topic = user_query
        for pattern in patterns_to_remove:
            topic = re.sub(pattern, '', topic, flags=re.IGNORECASE)
        
        # Clean up
        topic = topic.strip()
        
        # If topic is empty or too short, use original query
        if len(topic) < 3:
            topic = user_query
        
        return topic
    
    def _needs_refresh(self, existing_articles: List[Dict], topic: str) -> tuple[bool, str]:
        """
        Determine if we need to fetch new articles.
        
        Args:
            existing_articles: List of existing articles from search
            topic: The search topic
        
        Returns:
            Tuple of (needs_refresh: bool, reason: str)
        """
        # No articles found
        if not existing_articles:
            return True, "No existing articles found"
        
        # Not enough articles
        if len(existing_articles) < self.min_articles:
            return True, f"Only {len(existing_articles)} articles found (need {self.min_articles})"
        
        # Check freshness of articles
        try:
            # Get the most recent article
            articles_with_dates = [
                a for a in existing_articles 
                if a.get('metadata', {}).get('published_at')
            ]
            
            if not articles_with_dates:
                return True, "No articles with publication dates"
            
            # Find most recent article
            latest_article = max(
                articles_with_dates,
                key=lambda x: self._parse_date(x['metadata']['published_at'])
            )
            
            latest_date = self._parse_date(latest_article['metadata']['published_at'])
            age_hours = (datetime.now(timezone.utc) - latest_date).total_seconds() / 3600
            
            if age_hours > self.max_article_age_hours:
                return True, f"Latest article is {age_hours:.1f} hours old (threshold: {self.max_article_age_hours}h)"
            
        except Exception as e:
            logger.warning(f"Error checking article freshness: {e}")
            # If we can't determine freshness, don't fetch
            return False, "Could not determine article freshness"
        
        return False, "Existing articles are fresh and sufficient"
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string in various formats
        
        Returns:
            datetime object (timezone-aware)
        """
        # Try common formats
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Make timezone-aware if not already
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        # If all formats fail, return current time
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.now(timezone.utc)
    
    def _select_best_articles(self, articles: List[Dict], max_count: int) -> List[Dict]:
        """
        Select the best articles based on relevance and freshness.
        
        Args:
            articles: List of candidate articles
            max_count: Maximum number to select
        
        Returns:
            Filtered and sorted list of articles
        """
        if not articles:
            return []
        
        # Score each article
        scored_articles = []
        for article in articles:
            score = 0.0
            
            # Relevance score (from vector search similarity)
            if 'similarity' in article:
                score += article['similarity'] * 0.7  # 70% weight on relevance
            
            # Freshness score
            if article.get('metadata', {}).get('published_at'):
                try:
                    pub_date = self._parse_date(article['metadata']['published_at'])
                    age_hours = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600
                    # Newer articles get higher scores (exponential decay)
                    freshness = max(0, 1 - (age_hours / 168))  # Decay over 1 week
                    score += freshness * 0.3  # 30% weight on freshness
                except Exception:
                    pass
            
            scored_articles.append((score, article))
        
        # Sort by score (descending) and take top N
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in scored_articles[:max_count]]
