#!/usr/bin/env python3
"""
Test script for the vectorization module.
Run this to verify Phase 3 is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vectorization.embedder import TextEmbedder
from src.vectorization.pipeline import VectorizationPipeline
from src.database.db_manager import DatabaseManager


def test_embedder():
    """Test the text embedder."""
    print("\n" + "=" * 60)
    print("Testing Text Embedder")
    print("=" * 60)
    
    print("\n[1] Initializing embedder...")
    embedder = TextEmbedder()
    
    # Get model info
    print("\n[2] Model information:")
    info = embedder.get_model_info()
    print(f"   Model: {info['model_name']}")
    print(f"   Embedding dimension: {info['embedding_dimension']}")
    print(f"   Max sequence length: {info['max_sequence_length']}")
    
    # Test single text
    print("\n[3] Testing single text embedding...")
    text = "Artificial intelligence is transforming technology"
    embedding = embedder.embed_text(text)
    print(f"   Text: '{text}'")
    print(f"   Embedding shape: {embedding.shape}")
    print(f"   ✅ Single embedding generated")
    
    # Test batch
    print("\n[4] Testing batch embedding...")
    texts = [
        "Machine learning enables computers to learn",
        "Deep learning uses neural networks",
        "Natural language processing understands text"
    ]
    embeddings = embedder.embed_texts(texts, show_progress=False)
    print(f"   Generated {len(embeddings)} embeddings")
    print(f"   Shape: {embeddings.shape}")
    print(f"   ✅ Batch embeddings generated")
    
    # Test similarity
    print("\n[5] Testing similarity computation...")
    sim1 = embedder.compute_similarity(embeddings[0], embeddings[1])
    sim2 = embedder.compute_similarity(embeddings[0], embeddings[2])
    print(f"   Similarity (ML vs DL): {sim1:.4f}")
    print(f"   Similarity (ML vs NLP): {sim2:.4f}")
    print(f"   ✅ Similarity computation working")
    
    print("\n✅ Text embedder test completed!")
    return True


def test_vectorization_pipeline():
    """Test the vectorization pipeline."""
    print("\n" + "=" * 60)
    print("Testing Vectorization Pipeline")
    print("=" * 60)
    
    print("\n[1] Initializing pipeline...")
    pipeline = VectorizationPipeline()
    print("   ✅ Pipeline initialized")
    
    print("\n[2] Checking pipeline status...")
    status = pipeline.get_pipeline_status()
    print(f"   Total articles: {status['total_articles']}")
    print(f"   Vectorized: {status['vectorized_articles']}")
    print(f"   Pending: {status['pending_articles']}")
    print(f"   Completion: {status['completion_percentage']:.1f}%")
    
    if status['total_articles'] == 0:
        print("\n   ⚠️  No articles in database. Run test_ingestion.py first.")
        return False
    
    if status['pending_articles'] > 0:
        print(f"\n[3] Vectorizing {status['pending_articles']} articles...")
        stats = pipeline.vectorize_all_articles(batch_size=8, show_progress=True)
        print(f"   ✅ Processed: {stats['processed']}")
        print(f"   ✅ Successful: {stats['successful']}")
        if stats['failed'] > 0:
            print(f"   ⚠️  Failed: {stats['failed']}")
    else:
        print("\n[3] All articles already vectorized ✅")
    
    print("\n[4] Testing similarity search...")
    query = "technology and innovation"
    results = pipeline.search_similar_articles(query, top_k=3)
    print(f"   Query: '{query}'")
    
    if results:
        print(f"   Found {len(results)} similar articles:")
        for i, result in enumerate(results, 1):
            title = result['title'][:50] + "..." if len(result['title']) > 50 else result['title']
            print(f"\n   {i}. {title}")
            print(f"      Source: {result['source']}")
            print(f"      Similarity: {result['similarity_score']:.4f}")
        print("   ✅ Similarity search working")
    else:
        print("   ⚠️  No results found")
    
    print("\n[5] Final status...")
    final_status = pipeline.get_pipeline_status()
    print(f"   Completion: {final_status['completion_percentage']:.1f}%")
    
    print("\n✅ Vectorization pipeline test completed!")
    return True


def test_database_embeddings():
    """Test embedding storage in database."""
    print("\n" + "=" * 60)
    print("Testing Database Embedding Storage")
    print("=" * 60)
    
    db = DatabaseManager()
    
    print("\n[1] Checking database statistics...")
    stats = db.get_stats()
    print(f"   Total articles: {stats['total_articles']}")
    print(f"   With embeddings: {stats['articles_with_embeddings']}")
    print(f"   Without embeddings: {stats['articles_without_embeddings']}")
    
    if stats['articles_with_embeddings'] > 0:
        print("\n[2] Retrieving article with embedding...")
        articles = db.get_all_articles(limit=1)
        if articles and articles[0].get('embedding'):
            article = articles[0]
            print(f"   Article: {article['title'][:50]}...")
            print(f"   Embedding stored: ✅")
            
            # Check embedding size
            import numpy as np
            embedding_bytes = article['embedding']
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            print(f"   Embedding shape: {embedding.shape}")
            print(f"   ✅ Embedding retrieval working")
        else:
            print("   ⚠️  No embeddings found in database")
    else:
        print("\n[2] No articles with embeddings yet")
    
    print("\n✅ Database embedding test completed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI News Summarizer - Phase 3 Testing")
    print("Vectorization Module")
    print("=" * 60)
    
    results = {
        'embedder': False,
        'pipeline': False,
        'database': False
    }
    
    # Test 1: Embedder
    try:
        results['embedder'] = test_embedder()
    except Exception as e:
        print(f"\n❌ Embedder test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Database embeddings
    try:
        results['database'] = test_database_embeddings()
    except Exception as e:
        print(f"\n❌ Database embedding test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Vectorization pipeline
    try:
        results['pipeline'] = test_vectorization_pipeline()
    except Exception as e:
        print(f"\n❌ Vectorization pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Text Embedder:           {'✅ PASS' if results['embedder'] else '❌ FAIL'}")
    print(f"Database Storage:        {'✅ PASS' if results['database'] else '❌ FAIL'}")
    print(f"Vectorization Pipeline:  {'✅ PASS' if results['pipeline'] else '❌ FAIL'}")
    
    if all(results.values()):
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Phase 3 is complete!")
        print("=" * 60)
    elif not results['pipeline']:
        print("\n" + "=" * 60)
        print("⚠️  Note: Make sure you have articles in the database")
        print("Run: python test_ingestion.py")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
