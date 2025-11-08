"""
Retrieval pipeline for RAG (Retrieval-Augmented Generation).
Integrates database, vector store, and provides context for LLM summarization.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.retrieval.vector_store import VectorStore
from src.database.db_manager import DatabaseManager
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """Pipeline for retrieving relevant articles for RAG."""
    
    def __init__(
        self,
        collection_name: str = "news_articles",
        db_path: Optional[str] = None,
        vector_store_path: Optional[str] = None
    ):
        """
        Initialize the retrieval pipeline.
        
        Args:
            collection_name: ChromaDB collection name
            db_path: Database path (optional)
            vector_store_path: Vector store path (optional)
        """
        self.db = DatabaseManager(db_path=db_path)
        self.vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=vector_store_path
        )
        self.settings = get_settings()
        
        logger.info("RetrievalPipeline initialized successfully")
    
    def sync_database_to_vector_store(
        self,
        batch_size: int = 100,
        force_reindex: bool = False
    ) -> Dict[str, int]:
        """
        Sync articles from database to vector store.
        
        Args:
            batch_size: Batch size for processing
            force_reindex: If True, re-index all articles
        
        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting database to vector store sync...")
        
        # Get all articles from database
        all_articles = self.db.get_all_articles()
        
        if not all_articles:
            logger.warning("No articles in database to sync")
            return {'synced': 0, 'skipped': 0, 'failed': 0}
        
        # Get existing IDs in vector store if not forcing reindex
        existing_ids = set()
        if not force_reindex:
            try:
                vs_stats = self.vector_store.get_stats()
                if vs_stats['total_articles'] > 0:
                    # Get all IDs from vector store
                    peek_result = self.vector_store.collection.get(
                        limit=vs_stats['total_articles'],
                        include=[]
                    )
                    existing_ids = set(peek_result['ids'])
            except Exception as e:
                logger.warning(f"Could not get existing IDs: {e}")
        
        synced = 0
        skipped = 0
        failed = 0
        
        # Process in batches
        for i in range(0, len(all_articles), batch_size):
            batch = all_articles[i:i + batch_size]
            
            batch_ids = []
            batch_texts = []
            batch_metadatas = []
            
            for article in batch:
                article_id = str(article['id'])
                
                # Skip if already exists and not forcing reindex
                if not force_reindex and article_id in existing_ids:
                    skipped += 1
                    continue
                
                # Prepare text (combine title, description, content)
                text_parts = []
                if article.get('title'):
                    text_parts.append(article['title'])
                if article.get('description'):
                    text_parts.append(article['description'])
                if article.get('content'):
                    content = article['content']
                    # Remove NewsAPI truncation marker
                    if '[+' in content:
                        content = content.split('[+')[0].strip()
                    text_parts.append(content)
                
                text = ' '.join(text_parts)
                
                if not text.strip():
                    logger.warning(f"Article {article_id} has no text content")
                    failed += 1
                    continue
                
                # Prepare metadata
                metadata = {
                    'title': article.get('title', ''),
                    'source': article.get('source', 'Unknown'),
                    'author': article.get('author', 'Unknown'),
                    'published_at': article.get('published_at', ''),
                    'url': article.get('url', ''),
                    'fetched_at': article.get('fetched_at', '')
                }
                
                batch_ids.append(article_id)
                batch_texts.append(text)
                batch_metadatas.append(metadata)
            
            # Add batch to vector store
            if batch_ids:
                result = self.vector_store.add_articles(
                    article_ids=batch_ids,
                    texts=batch_texts,
                    metadatas=batch_metadatas
                )
                synced += result['added']
                failed += result['failed']
        
        stats = {
            'synced': synced,
            'skipped': skipped,
            'failed': failed,
            'total': len(all_articles)
        }
        
        logger.info(f"Sync complete: {stats}")
        return stats
    
    def retrieve_for_query(
        self,
        query: str,
        top_k: int = 5,
        source_filter: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant articles for a query (main RAG retrieval method).
        
        Args:
            query: Search query
            top_k: Number of articles to retrieve
            source_filter: Optional source name filter
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of relevant articles with metadata
        """
        # Build where clause for filtering
        where = None
        if source_filter:
            where = {"source": source_filter}
        
        # Search vector store
        results = self.vector_store.search(
            query=query,
            n_results=top_k,
            where=where
        )
        
        # Filter by minimum similarity
        filtered_results = [
            r for r in results
            if r['similarity'] >= min_similarity
        ]
        
        logger.info(f"Retrieved {len(filtered_results)} articles for query: '{query[:50]}...'")
        return filtered_results
    
    def retrieve_context_for_summarization(
        self,
        topic: str,
        max_articles: int = 5,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Retrieve and format context for LLM summarization.
        
        Args:
            topic: Topic to retrieve articles about
            max_articles: Maximum number of articles
            max_tokens: Approximate max tokens for context
        
        Returns:
            Dictionary with formatted context and metadata
        """
        # Retrieve relevant articles with minimum similarity threshold
        # Use lower threshold for broad queries, higher for specific ones
        min_sim = 0.2 if len(topic.split()) <= 1 else 0.4
        articles = self.retrieve_for_query(
            query=topic,
            top_k=max_articles,
            min_similarity=min_sim
        )
        
        if not articles:
            return {
                'context': '',
                'articles': [],
                'sources': [],
                'article_count': 0
            }
        
        # Format context for LLM
        context_parts = []
        sources = []
        
        for i, article in enumerate(articles, 1):
            metadata = article['metadata']
            
            # Format article
            article_text = f"""
                Article {i}:
                Title: {metadata.get('title', 'Untitled')}
                Source: {metadata.get('source', 'Unknown')}
                Content: {article['document'][:500]}...
                URL: {metadata.get('url', 'N/A')}
                """
            context_parts.append(article_text.strip())
            
            # Track sources
            source_info = {
                'title': metadata.get('title', 'Untitled'),
                'source': metadata.get('source', 'Unknown'),
                'url': metadata.get('url', ''),
                'published_at': metadata.get('published_at', ''),
                'similarity': article['similarity']
            }
            sources.append(source_info)
        
        # Combine context
        full_context = "\n\n---\n\n".join(context_parts)
        
        # Truncate if too long (rough token estimation: 1 token ≈ 4 chars)
        if len(full_context) > max_tokens * 4:
            full_context = full_context[:max_tokens * 4] + "..."
        
        return {
            'context': full_context,
            'articles': articles,
            'sources': sources,
            'article_count': len(articles),
            'topic': topic
        }
    
    def search_by_topic(
        self,
        topic: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search articles by topic.
        
        Args:
            topic: Topic to search for
            top_k: Number of results
        
        Returns:
            List of articles
        """
        return self.retrieve_for_query(query=topic, top_k=top_k)
    
    def search_by_source(
        self,
        query: str,
        source: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search articles from a specific source.
        
        Args:
            query: Search query
            source: Source name
            top_k: Number of results
        
        Returns:
            List of articles
        """
        return self.retrieve_for_query(
            query=query,
            top_k=top_k,
            source_filter=source
        )
    
    def get_similar_articles(
        self,
        article_id: int,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find articles similar to a given article.
        
        Args:
            article_id: Reference article ID
            top_k: Number of similar articles to return
        
        Returns:
            List of similar articles
        """
        # Get the reference article
        article = self.db.get_article_by_id(article_id)
        if not article:
            logger.error(f"Article {article_id} not found")
            return []
        
        # Use article title and description as query
        query_parts = []
        if article.get('title'):
            query_parts.append(article['title'])
        if article.get('description'):
            query_parts.append(article['description'])
        
        query = ' '.join(query_parts)
        
        # Search for similar articles
        results = self.retrieve_for_query(query=query, top_k=top_k + 1)
        
        # Remove the reference article itself
        results = [r for r in results if r['id'] != str(article_id)]
        
        return results[:top_k]
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get retrieval pipeline status.
        
        Returns:
            Dictionary with status information
        """
        db_stats = self.db.get_stats()
        vs_stats = self.vector_store.get_stats()
        
        return {
            'database': {
                'total_articles': db_stats['total_articles'],
                'articles_by_source': db_stats['articles_by_source']
            },
            'vector_store': {
                'total_articles': vs_stats['total_articles'],
                'collection_name': vs_stats['collection_name'],
                'embedding_model': vs_stats['embedding_model'],
                'sources': vs_stats['sources']
            },
            'sync_status': {
                'in_sync': db_stats['total_articles'] == vs_stats['total_articles'],
                'db_count': db_stats['total_articles'],
                'vs_count': vs_stats['total_articles'],
                'difference': db_stats['total_articles'] - vs_stats['total_articles']
            }
        }


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Retrieval Pipeline - Testing")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        print("\n[1/5] Initializing retrieval pipeline...")
        pipeline = RetrievalPipeline()
        print("✅ Pipeline initialized")
        
        # Check status
        print("\n[2/5] Checking pipeline status...")
        status = pipeline.get_pipeline_status()
        print(f"   Database articles: {status['database']['total_articles']}")
        print(f"   Vector store articles: {status['vector_store']['total_articles']}")
        print(f"   In sync: {status['sync_status']['in_sync']}")
        
        # Sync if needed
        if not status['sync_status']['in_sync']:
            print(f"\n[3/5] Syncing {status['sync_status']['difference']} articles...")
            sync_stats = pipeline.sync_database_to_vector_store()
            print(f"   ✅ Synced: {sync_stats['synced']}")
            print(f"   ⏭️  Skipped: {sync_stats['skipped']}")
            if sync_stats['failed'] > 0:
                print(f"   ⚠️  Failed: {sync_stats['failed']}")
        else:
            print("\n[3/5] Database and vector store already in sync ✅")
        
        # Test retrieval
        print("\n[4/5] Testing article retrieval...")
        query = "technology and innovation"
        results = pipeline.retrieve_for_query(query, top_k=3)
        print(f"   Query: '{query}'")
        print(f"   Found {len(results)} articles:")
        for i, result in enumerate(results, 1):
            title = result['metadata'].get('title', 'Untitled')[:50]
            print(f"\n   {i}. {title}...")
            print(f"      Source: {result['metadata'].get('source', 'Unknown')}")
            print(f"      Similarity: {result['similarity']:.4f}")
        
        # Test context retrieval
        print("\n[5/5] Testing context retrieval for summarization...")
        context = pipeline.retrieve_context_for_summarization(
            topic="artificial intelligence",
            max_articles=2
        )
        print(f"   Topic: {context['topic']}")
        print(f"   Retrieved {context['article_count']} articles")
        print(f"   Context length: {len(context['context'])} characters")
        
        print("\n" + "=" * 60)
        print("✅ Retrieval pipeline test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
