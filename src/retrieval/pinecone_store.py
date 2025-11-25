"""
Pinecone vector store implementation.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
import numpy as np
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)


def estimate_metadata_size(metadata: Dict[str, Any]) -> int:
    """
    Estimate the size of metadata in bytes.
    
    Args:
        metadata: Metadata dictionary
    
    Returns:
        Estimated size in bytes
    """
    return len(json.dumps(metadata).encode('utf-8'))


class PineconeStore:
    """Pinecone vector store for semantic search."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: str = "news-summarizer",
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
            
            # Add content if available (truncate to fit metadata limits)
            # Pinecone has a 40KB limit per vector metadata
            # Keep content short to leave room for other fields
            if article.get('content'):
                content = article['content']
                # Truncate to ~10KB (10,000 chars) to be safe
                # This leaves room for title, source, url, etc.
                max_content_length = 10000
                if len(content) > max_content_length:
                    content = content[:max_content_length] + '...'
                    logger.debug(f"Truncated content from {len(article['content'])} to {max_content_length} chars")
                metadata['content'] = content
            
            # Validate metadata size (Pinecone limit is 40KB)
            metadata_size = estimate_metadata_size(metadata)
            if metadata_size > 40960:  # 40KB in bytes
                logger.warning(f"Metadata size ({metadata_size} bytes) exceeds 40KB limit for article {article['id']}")
                # Further truncate content if needed
                if 'content' in metadata:
                    # Reduce content by half and try again
                    metadata['content'] = metadata['content'][:len(metadata['content'])//2] + '...'
                    metadata_size = estimate_metadata_size(metadata)
                    logger.info(f"Reduced metadata size to {metadata_size} bytes")
            
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
        
        # Format results to match ChromaDB format
        matches = []
        for match in results['matches']:
            similarity = match['score'] # score will be determined by Pinecone's cosine similarity (0-1 range, higher is more similar)
            
            if similarity < min_similarity:
                continue
            
            metadata = match['metadata']
            
            # Format to match ChromaDB output (with 'document' field)
            matches.append({
                'id': match['id'],
                'similarity': similarity,
                'document': metadata.get('content', ''),
                'metadata': metadata
            })

        # Log similarity scores for debugging
        if matches:
            sample_scores = [f"{m['id']}:{m['similarity']:.3f}" for m in matches[:3]]
            logger.info(f"Found {len(matches)} matches (min_similarity={min_similarity}), sample scores: {sample_scores}")
            logger.info(f"Sample match: {matches[0]}")  # Log the first match object
        else:
            logger.info(f"Found 0 matches (min_similarity={min_similarity})")
        
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
    
    def get_stats(self) -> dict:
        """Get index statistics (for compatibility with VectorStore interface)."""
        stats = self.index.describe_index_stats()
        return {
            'total': stats.get('total_vector_count', 0),
            'dimension': stats.get('dimension', 384)
        }
    
    def search_by_text(self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search using text query (for compatibility with VectorStore interface).
        Converts text to embedding first, then searches.
        
        Args:
            query: Text query string
            top_k: Number of results
            filter_dict: Metadata filters
            
        Returns:
            List of matching articles
        """
        from src.vectorization.embedder import TextEmbedder
        
        # Convert text to embedding
        embedder = TextEmbedder()
        query_embedding = embedder.embed_text(query)
        
        # Search with embedding
        return self.search(
            query_embedding=query_embedding,
            top_k=top_k,
            min_similarity=0.0,
            filter_dict=filter_dict
        )
    
    def clear_index(self):
        """Clear all vectors from the Pinecone index."""
        try:
            # Delete all vectors by deleting all IDs
            stats = self.index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            
            if total_vectors > 0:
                # Delete all vectors in the default namespace
                self.index.delete(delete_all=True)
                logger.info(f"Cleared {total_vectors} vectors from Pinecone index")
            else:
                logger.info("Pinecone index is already empty")
                
        except Exception as e:
            logger.error(f"Error clearing Pinecone index: {e}")
            raise