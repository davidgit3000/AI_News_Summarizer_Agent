"""
Embedding generator for converting text to vector representations.
Uses Sentence Transformers for high-quality embeddings.
"""

import logging
from typing import List, Dict, Optional, Union, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextEmbedder:
    """Generates embeddings for text using Sentence Transformers."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the text embedder.
        
        Args:
            model_name: Name of the sentence transformer model.
                       If None, uses model from settings.
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        # Get embedding dimension
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
        
        Returns:
            Numpy array of embeddings
        """
        if not text or not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return np.zeros(self.embedding_dim)
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
        
        Returns:
            Numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        if not texts:
            logger.warning("Empty text list provided")
            return np.array([])
        
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def embed_article(self, article: Dict) -> np.ndarray:
        """
        Generate embedding for an article.
        Combines title, description, and content.
        
        Args:
            article: Article dictionary with 'title', 'description', 'content'
        
        Returns:
            Numpy array of embeddings
        """
        # Combine article fields
        text_parts = []
        
        if article.get('title'):
            text_parts.append(article['title'])
        
        if article.get('description'):
            text_parts.append(article['description'])
        
        if article.get('content'):
            # Content from NewsAPI is often truncated with [+X chars]
            content = article['content']
            # Remove truncation marker
            if '[+' in content:
                content = content.split('[+')[0].strip()
            text_parts.append(content)
        
        # Combine all parts
        combined_text = ' '.join(text_parts)
        
        if not combined_text.strip():
            logger.warning(f"Article has no text content: {article.get('url', 'Unknown')}")
            return np.zeros(self.embedding_dim)
        
        return self.embed_text(combined_text)
    
    def embed_articles(
        self,
        articles: List[Dict],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple articles.
        
        Args:
            articles: List of article dictionaries
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
        
        Returns:
            List of numpy arrays (embeddings)
        """
        if not articles:
            logger.warning("Empty article list provided")
            return []
        
        logger.info(f"Processing {len(articles)} articles for embedding...")
        
        # Prepare texts
        texts = []
        for article in articles:
            text_parts = []
            
            if article.get('title'):
                text_parts.append(article['title'])
            if article.get('description'):
                text_parts.append(article['description'])
            if article.get('content'):
                content = article['content']
                if '[+' in content:
                    content = content.split('[+')[0].strip()
                text_parts.append(content)
            
            combined_text = ' '.join(text_parts)
            texts.append(combined_text if combined_text.strip() else "")
        
        # Generate embeddings
        embeddings = self.embed_texts(texts, batch_size, show_progress)
        
        # Convert to list of arrays
        return [embeddings[i] for i in range(len(embeddings))]
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Similarity score (0 to 1)
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # Clip to [0, 1] range
        return float(np.clip(similarity, 0, 1))
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to a query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
        
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        if not candidate_embeddings:
            return []
        
        # Compute similarities
        similarities = []
        for idx, candidate in enumerate(candidate_embeddings):
            sim = self.compute_similarity(query_embedding, candidate)
            similarities.append((idx, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return similarities[:top_k]
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dim,
            'max_sequence_length': self.model.max_seq_length,
        }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Text Embedder - Testing")
    print("=" * 60)
    
    # Initialize embedder
    print("\n[1/5] Initializing embedder...")
    embedder = TextEmbedder()
    
    # Get model info
    print("\n[2/5] Model information:")
    info = embedder.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Test single text embedding
    print("\n[3/5] Testing single text embedding...")
    text = "Artificial intelligence is transforming the world"
    embedding = embedder.embed_text(text)
    print(f"   Text: {text}")
    print(f"   Embedding shape: {embedding.shape}")
    print(f"   First 5 values: {embedding[:5]}")
    
    # Test multiple texts
    print("\n[4/5] Testing batch embedding...")
    texts = [
        "Machine learning is a subset of AI",
        "Deep learning uses neural networks",
        "Natural language processing enables text understanding"
    ]
    embeddings = embedder.embed_texts(texts, show_progress=False)
    print(f"   Generated {len(embeddings)} embeddings")
    print(f"   Shape: {embeddings.shape}")
    
    # Test similarity
    print("\n[5/5] Testing similarity computation...")
    sim1 = embedder.compute_similarity(embeddings[0], embeddings[1])
    sim2 = embedder.compute_similarity(embeddings[0], embeddings[2])
    print(f"   Similarity (text 1 vs text 2): {sim1:.4f}")
    print(f"   Similarity (text 1 vs text 3): {sim2:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ Embedder test completed!")
    print("=" * 60)
