"""
Vectorization pipeline for generating and storing article embeddings.
Integrates TextEmbedder with DatabaseManager.
"""

import logging
from typing import List, Dict, Optional, Any
import numpy as np
from tqdm import tqdm

from src.vectorization.embedder import TextEmbedder
from src.database.db_manager import DatabaseManager
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorizationPipeline:
    """Pipeline for generating and storing article embeddings."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        db_path: Optional[str] = None
    ):
        """
        Initialize the vectorization pipeline.
        
        Args:
            model_name: Embedding model name (optional, uses config if not provided)
            db_path: Database path (optional, uses config if not provided)
        """
        self.embedder = TextEmbedder(model_name=model_name)
        self.db = DatabaseManager(db_path=db_path)
        self.settings = get_settings()
        
        logger.info("VectorizationPipeline initialized successfully")
    
    def vectorize_article(self, article_id: int) -> bool:
        """
        Generate and store embedding for a single article.
        
        Args:
            article_id: Article ID from database
        
        Returns:
            True if successful
        """
        # Get article from database
        article = self.db.get_article_by_id(article_id)
        if not article:
            logger.error(f"Article not found: {article_id}")
            return False
        
        # Generate embedding
        embedding = self.embedder.embed_article(article)
        
        # Store in database
        success = self.db.update_embedding(article_id, embedding)
        
        if success:
            logger.debug(f"Vectorized article {article_id}: {article.get('title', 'Untitled')[:50]}")
        
        return success
    
    def vectorize_articles(
        self,
        article_ids: Optional[List[int]] = None,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> Dict[str, int]:
        """
        Generate and store embeddings for multiple articles.
        
        Args:
            article_ids: List of article IDs. If None, processes all articles without embeddings.
            batch_size: Batch size for embedding generation
            show_progress: Whether to show progress bar
        
        Returns:
            Dictionary with processing statistics
        """
        # Get articles to process
        if article_ids is None:
            articles = self.db.get_articles_without_embeddings()
            logger.info(f"Found {len(articles)} articles without embeddings")
        else:
            articles = [self.db.get_article_by_id(aid) for aid in article_ids]
            articles = [a for a in articles if a is not None]
            logger.info(f"Processing {len(articles)} specified articles")
        
        if not articles:
            logger.info("No articles to vectorize")
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        # Process in batches
        successful = 0
        failed = 0
        
        # Use tqdm for progress if enabled
        iterator = tqdm(articles, desc="Vectorizing articles") if show_progress else articles
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            # Generate embeddings for batch
            embeddings = self.embedder.embed_articles(
                batch,
                batch_size=batch_size,
                show_progress=False
            )
            
            # Store embeddings
            for article, embedding in zip(batch, embeddings):
                success = self.db.update_embedding(article['id'], embedding)
                if success:
                    successful += 1
                else:
                    failed += 1
                
                if show_progress and hasattr(iterator, 'update'):
                    iterator.update(1)
        
        stats = {
            'processed': len(articles),
            'successful': successful,
            'failed': failed
        }
        
        logger.info(f"Vectorization complete: {stats}")
        return stats
    
    def vectorize_all_articles(
        self,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> Dict[str, int]:
        """
        Generate embeddings for all articles that don't have them.
        
        Args:
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
        
        Returns:
            Dictionary with processing statistics
        """
        logger.info("Starting full database vectorization...")
        return self.vectorize_articles(
            article_ids=None,
            batch_size=batch_size,
            show_progress=show_progress
        )
    
    def re_vectorize_all(
        self,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> Dict[str, int]:
        """
        Re-generate embeddings for ALL articles (including those with existing embeddings).
        Useful when changing embedding models.
        
        Args:
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
        
        Returns:
            Dictionary with processing statistics
        """
        logger.info("Re-vectorizing all articles in database...")
        
        # Get all articles
        all_articles = self.db.get_all_articles()
        article_ids = [article['id'] for article in all_articles]
        
        return self.vectorize_articles(
            article_ids=article_ids,
            batch_size=batch_size,
            show_progress=show_progress
        )
    
    def get_embedding(self, article_id: int) -> Optional[np.ndarray]:
        """
        Retrieve embedding for an article from database.
        
        Args:
            article_id: Article ID
        
        Returns:
            Numpy array of embeddings, or None if not found
        """
        article = self.db.get_article_by_id(article_id)
        if not article or not article.get('embedding'):
            return None
        
        # Convert bytes back to numpy array
        embedding_bytes = article['embedding']
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        
        return embedding
    
    def search_similar_articles(
        self,
        query_text: str,
        top_k: int = 5,
        source_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for articles similar to a query text.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            source_filter: Optional source name to filter by
        
        Returns:
            List of article dictionaries with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query_text)
        
        # Get all articles with embeddings
        if source_filter:
            articles = self.db.get_articles_by_source(source_filter)
        else:
            articles = self.db.get_all_articles()
        
        # Filter articles with embeddings
        articles_with_embeddings = [
            a for a in articles if a.get('embedding') is not None
        ]
        
        if not articles_with_embeddings:
            logger.warning("No articles with embeddings found")
            return []
        
        # Compute similarities
        similarities = []
        for article in articles_with_embeddings:
            embedding_bytes = article['embedding']
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            similarity = self.embedder.compute_similarity(query_embedding, embedding)
            
            similarities.append({
                'article': article,
                'similarity': similarity
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top k
        results = []
        for item in similarities[:top_k]:
            result = item['article'].copy()
            result['similarity_score'] = item['similarity']
            # Remove embedding from result (too large)
            result.pop('embedding', None)
            results.append(result)
        
        return results
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current vectorization pipeline status.
        
        Returns:
            Dictionary with status information
        """
        db_stats = self.db.get_stats()
        model_info = self.embedder.get_model_info()
        
        total = db_stats['total_articles']
        with_embeddings = db_stats['articles_with_embeddings']
        without_embeddings = db_stats['articles_without_embeddings']
        
        status = {
            'embedding_model': model_info['model_name'],
            'embedding_dimension': model_info['embedding_dimension'],
            'total_articles': total,
            'vectorized_articles': with_embeddings,
            'pending_articles': without_embeddings,
            'completion_percentage': (with_embeddings / total * 100) if total > 0 else 0
        }
        
        return status


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Vectorization Pipeline - Testing")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        print("\n[1/5] Initializing pipeline...")
        pipeline = VectorizationPipeline()
        print("✅ Pipeline initialized")
        
        # Check status
        print("\n[2/5] Checking pipeline status...")
        status = pipeline.get_pipeline_status()
        print(f"   Model: {status['embedding_model']}")
        print(f"   Embedding dimension: {status['embedding_dimension']}")
        print(f"   Total articles: {status['total_articles']}")
        print(f"   Vectorized: {status['vectorized_articles']}")
        print(f"   Pending: {status['pending_articles']}")
        print(f"   Completion: {status['completion_percentage']:.1f}%")
        
        if status['pending_articles'] > 0:
            # Vectorize articles
            print(f"\n[3/5] Vectorizing {status['pending_articles']} articles...")
            stats = pipeline.vectorize_all_articles(batch_size=16)
            print(f"   ✅ Processed: {stats['processed']}")
            print(f"   ✅ Successful: {stats['successful']}")
            if stats['failed'] > 0:
                print(f"   ⚠️  Failed: {stats['failed']}")
        else:
            print("\n[3/5] All articles already vectorized ✅")
        
        # Test similarity search
        print("\n[4/5] Testing similarity search...")
        query = "artificial intelligence and machine learning"
        results = pipeline.search_similar_articles(query, top_k=3)
        print(f"   Query: '{query}'")
        print(f"   Found {len(results)} similar articles:")
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. {result['title'][:60]}...")
            print(f"      Source: {result['source']}")
            print(f"      Similarity: {result['similarity_score']:.4f}")
        
        # Final status
        print("\n[5/5] Final status...")
        final_status = pipeline.get_pipeline_status()
        print(f"   Vectorized: {final_status['vectorized_articles']}/{final_status['total_articles']}")
        print(f"   Completion: {final_status['completion_percentage']:.1f}%")
        
        print("\n" + "=" * 60)
        print("✅ Vectorization pipeline test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
