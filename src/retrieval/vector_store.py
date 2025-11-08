"""
Vector store manager using ChromaDB for semantic search.
Handles article indexing, retrieval, and similarity search with metadata filtering.
"""

import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """Manages ChromaDB vector store for article retrieval."""
    
    def __init__(
        self,
        collection_name: str = "news_articles",
        persist_directory: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
            embedding_model: Embedding model name (uses config if None)
        """
        settings_config = get_settings()
        
        # Set up persistence directory
        self.persist_directory = persist_directory or settings_config.vector_store_path
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Set up embedding function
        self.embedding_model = embedding_model or settings_config.embedding_model
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )
        
        # Get or create collection
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "News articles for RAG"}
        )
        
        logger.info(f"VectorStore initialized: {self.collection_name}")
        logger.info(f"Persist directory: {self.persist_directory}")
        logger.info(f"Collection size: {self.collection.count()}")
    
    def add_article(
        self,
        article_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a single article to the vector store.
        
        Args:
            article_id: Unique article identifier
            text: Article text (will be embedded automatically)
            metadata: Article metadata (source, date, etc.)
        
        Returns:
            True if successful
        """
        try:
            self.collection.add(
                ids=[str(article_id)],
                documents=[text],
                metadatas=[metadata] if metadata else None
            )
            logger.debug(f"Added article {article_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding article {article_id}: {e}")
            return False
    
    def add_articles(
        self,
        article_ids: List[str],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, int]:
        """
        Add multiple articles to the vector store in batch.
        
        Args:
            article_ids: List of unique article identifiers
            texts: List of article texts
            metadatas: List of article metadata dictionaries
        
        Returns:
            Dictionary with statistics
        """
        if not article_ids or not texts:
            logger.warning("Empty article list provided")
            return {'added': 0, 'failed': 0}
        
        if len(article_ids) != len(texts):
            raise ValueError("article_ids and texts must have same length")
        
        try:
            # Convert IDs to strings
            str_ids = [str(aid) for aid in article_ids]
            
            # Clean metadatas - remove None values as ChromaDB doesn't accept them
            cleaned_metadatas = None
            if metadatas:
                cleaned_metadatas = []
                for metadata in metadatas:
                    if metadata:
                        # Remove None values from metadata dict
                        cleaned_meta = {k: v for k, v in metadata.items() if v is not None}
                        cleaned_metadatas.append(cleaned_meta)
                    else:
                        cleaned_metadatas.append({})
            
            # Add to collection
            self.collection.add(
                ids=str_ids,
                documents=texts,
                metadatas=cleaned_metadatas
            )
            
            logger.info(f"Added {len(article_ids)} articles to vector store")
            return {'added': len(article_ids), 'failed': 0}
            
        except Exception as e:
            logger.error(f"Error adding articles in batch: {e}")
            return {'added': 0, 'failed': len(article_ids)}
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar articles using semantic search.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            where: Metadata filter (e.g., {"source": "BBC News"})
            where_document: Document content filter
        
        Returns:
            List of result dictionaries with article data and scores
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i],
                        'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    formatted_results.append(result)
            
            logger.debug(f"Search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def search_by_source(
        self,
        query: str,
        source: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search articles from a specific source.
        
        Args:
            query: Search query
            source: Source name to filter by
            n_results: Number of results
        
        Returns:
            List of results
        """
        return self.search(
            query=query,
            n_results=n_results,
            where={"source": source}
        )
    
    def search_by_date_range(
        self,
        query: str,
        start_date: str,
        end_date: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search articles within a date range.
        
        Args:
            query: Search query
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            n_results: Number of results
        
        Returns:
            List of results
        """
        return self.search(
            query=query,
            n_results=n_results,
            where={
                "$and": [
                    {"published_at": {"$gte": start_date}},
                    {"published_at": {"$lte": end_date}}
                ]
            }
        )
    
    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific article by ID.
        
        Args:
            article_id: Article ID
        
        Returns:
            Article dictionary or None
        """
        try:
            result = self.collection.get(
                ids=[str(article_id)],
                include=["documents", "metadatas"]
            )
            
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0] if result['metadatas'] else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving article {article_id}: {e}")
            return None
    
    def delete_article(self, article_id: str) -> bool:
        """
        Delete an article from the vector store.
        
        Args:
            article_id: Article ID
        
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[str(article_id)])
            logger.debug(f"Deleted article {article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            return False
    
    def update_article(
        self,
        article_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an article's text or metadata.
        
        Args:
            article_id: Article ID
            text: New text (optional)
            metadata: New metadata (optional)
        
        Returns:
            True if successful
        """
        try:
            update_params = {"ids": [str(article_id)]}
            
            if text is not None:
                update_params["documents"] = [text]
            if metadata is not None:
                update_params["metadatas"] = [metadata]
            
            self.collection.update(**update_params)
            logger.debug(f"Updated article {article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating article {article_id}: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """
        Delete all articles from the collection.
        
        Returns:
            True if successful
        """
        try:
            # Delete the collection
            self.client.delete_collection(name=self.collection_name)
            
            # Recreate it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "News articles for RAG"}
            )
            
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary with statistics
        """
        count = self.collection.count()
        
        # Try to get sample metadata to determine sources
        sources = set()
        if count > 0:
            try:
                sample = self.collection.get(
                    limit=min(100, count),
                    include=["metadatas"]
                )
                if sample['metadatas']:
                    sources = {m.get('source', 'Unknown') for m in sample['metadatas'] if m}
            except Exception as e:
                logger.warning(f"Could not retrieve source stats: {e}")
        
        return {
            'collection_name': self.collection_name,
            'total_articles': count,
            'embedding_model': self.embedding_model,
            'persist_directory': self.persist_directory,
            'sources': list(sources)
        }
    
    def peek(self, limit: int = 5) -> Dict[str, Any]:
        """
        Peek at a few articles in the collection.
        
        Args:
            limit: Number of articles to retrieve
        
        Returns:
            Dictionary with sample articles
        """
        try:
            return self.collection.peek(limit=limit)
        except Exception as e:
            logger.error(f"Error peeking collection: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("ChromaDB Vector Store - Testing")
    print("=" * 60)
    
    # Initialize vector store
    print("\n[1/5] Initializing vector store...")
    store = VectorStore(collection_name="test_articles")
    
    # Get initial stats
    print("\n[2/5] Initial statistics:")
    stats = store.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Add test articles
    print("\n[3/5] Adding test articles...")
    test_articles = [
        {
            'id': 'test1',
            'text': 'Artificial intelligence is revolutionizing technology and changing how we work.',
            'metadata': {'source': 'Tech News', 'published_at': '2024-01-01'}
        },
        {
            'id': 'test2',
            'text': 'Machine learning models are becoming more sophisticated and powerful.',
            'metadata': {'source': 'AI Weekly', 'published_at': '2024-01-02'}
        },
        {
            'id': 'test3',
            'text': 'Climate change is affecting weather patterns around the world.',
            'metadata': {'source': 'Science Daily', 'published_at': '2024-01-03'}
        }
    ]
    
    ids = [a['id'] for a in test_articles]
    texts = [a['text'] for a in test_articles]
    metadatas = [a['metadata'] for a in test_articles]
    
    result = store.add_articles(ids, texts, metadatas)
    print(f"   Added: {result['added']} articles")
    
    # Search
    print("\n[4/5] Testing semantic search...")
    query = "AI and machine learning"
    results = store.search(query, n_results=2)
    print(f"   Query: '{query}'")
    print(f"   Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. ID: {result['id']}")
        print(f"      Text: {result['document'][:60]}...")
        print(f"      Similarity: {result['similarity']:.4f}")
    
    # Final stats
    print("\n[5/5] Final statistics:")
    final_stats = store.get_stats()
    print(f"   Total articles: {final_stats['total_articles']}")
    
    print("\n" + "=" * 60)
    print("✅ Vector store test completed!")
    print("=" * 60)
