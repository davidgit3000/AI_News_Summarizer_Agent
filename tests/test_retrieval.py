#!/usr/bin/env python3
"""
Test script for the retrieval module (Phase 4).
Run this to verify RAG retrieval is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.retrieval.vector_store import VectorStore
from src.retrieval.pipeline import RetrievalPipeline
from src.database.db_manager import DatabaseManager


def test_vector_store():
    """Test ChromaDB vector store."""
    print("\n" + "=" * 60)
    print("Testing ChromaDB Vector Store")
    print("=" * 60)
    
    print("\n[1] Initializing vector store...")
    store = VectorStore(collection_name="test_retrieval")
    
    print("\n[2] Getting initial statistics...")
    stats = store.get_stats()
    print(f"   Collection: {stats['collection_name']}")
    print(f"   Total articles: {stats['total_articles']}")
    print(f"   Embedding model: {stats['embedding_model']}")
    
    print("\n[3] Adding test articles...")
    test_data = [
        {
            'id': 'test_ai_1',
            'text': 'Artificial intelligence and machine learning are transforming technology.',
            'metadata': {'source': 'Tech News', 'published_at': '2024-01-01'}
        },
        {
            'id': 'test_ai_2',
            'text': 'Deep learning neural networks achieve breakthrough in image recognition.',
            'metadata': {'source': 'AI Weekly', 'published_at': '2024-01-02'}
        },
        {
            'id': 'test_climate',
            'text': 'Climate change impacts global weather patterns and ecosystems.',
            'metadata': {'source': 'Science Daily', 'published_at': '2024-01-03'}
        }
    ]
    
    ids = [d['id'] for d in test_data]
    texts = [d['text'] for d in test_data]
    metadatas = [d['metadata'] for d in test_data]
    
    result = store.add_articles(ids, texts, metadatas)
    print(f"   ✅ Added {result['added']} articles")
    
    print("\n[4] Testing semantic search...")
    query = "AI and machine learning"
    results = store.search(query, n_results=2)
    print(f"   Query: '{query}'")
    print(f"   Found {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"\n   {i}. ID: {r['id']}")
        print(f"      Text: {r['document'][:60]}...")
        print(f"      Similarity: {r['similarity']:.4f}")
    
    print("\n[5] Testing metadata filtering...")
    results = store.search_by_source(query, source="Tech News", n_results=1)
    print(f"   Filtered by source 'Tech News': {len(results)} result(s)")
    if results:
        print(f"   ✅ Found: {results[0]['id']}")
    
    # Cleanup
    print("\n[6] Cleaning up test collection...")
    store.clear_collection()
    print("   ✅ Test collection cleared")
    
    print("\n✅ Vector store test completed!")
    return True


def test_retrieval_pipeline():
    """Test the full retrieval pipeline."""
    print("\n" + "=" * 60)
    print("Testing Retrieval Pipeline")
    print("=" * 60)
    
    print("\n[1] Initializing pipeline...")
    pipeline = RetrievalPipeline()
    print("   ✅ Pipeline initialized")
    
    print("\n[2] Checking pipeline status...")
    status = pipeline.get_pipeline_status()
    print(f"   Database articles: {status['database']['total_articles']}")
    print(f"   Vector store articles: {status['vector_store']['total_articles']}")
    print(f"   In sync: {status['sync_status']['in_sync']}")
    
    if status['database']['total_articles'] == 0:
        print("\n   ⚠️  No articles in database. Run test_ingestion.py first.")
        return False
    
    print("\n[3] Syncing database to vector store...")
    if not status['sync_status']['in_sync']:
        sync_stats = pipeline.sync_database_to_vector_store()
        print(f"   ✅ Synced: {sync_stats['synced']}")
        print(f"   ⏭️  Skipped: {sync_stats['skipped']}")
        if sync_stats['failed'] > 0:
            print(f"   ⚠️  Failed: {sync_stats['failed']}")
    else:
        print("   ✅ Already in sync")
    
    print("\n[4] Testing article retrieval...")
    query = "technology and innovation"
    results = pipeline.retrieve_for_query(query, top_k=3)
    print(f"   Query: '{query}'")
    
    if results:
        print(f"   Found {len(results)} articles:")
        for i, result in enumerate(results, 1):
            title = result['metadata'].get('title', 'Untitled')
            title = title[:50] + "..." if len(title) > 50 else title
            print(f"\n   {i}. {title}")
            print(f"      Source: {result['metadata'].get('source', 'Unknown')}")
            print(f"      Similarity: {result['similarity']:.4f}")
        print("   ✅ Retrieval working")
    else:
        print("   ⚠️  No results found")
    
    print("\n[5] Testing context retrieval for RAG...")
    context = pipeline.retrieve_context_for_summarization(
        topic="artificial intelligence",
        max_articles=2
    )
    print(f"   Topic: '{context['topic']}'")
    print(f"   Retrieved: {context['article_count']} articles")
    print(f"   Context length: {len(context['context'])} characters")
    print(f"   Sources: {len(context['sources'])}")
    
    if context['sources']:
        print("\n   Sources retrieved:")
        for i, source in enumerate(context['sources'], 1):
            print(f"   {i}. {source['title'][:40]}... (similarity: {source['similarity']:.4f})")
        print("   ✅ Context retrieval working")
    
    print("\n[6] Final status check...")
    final_status = pipeline.get_pipeline_status()
    print(f"   Vector store: {final_status['vector_store']['total_articles']} articles")
    print(f"   Sync status: {'✅ In sync' if final_status['sync_status']['in_sync'] else '⚠️  Out of sync'}")
    
    print("\n✅ Retrieval pipeline test completed!")
    return True


def test_rag_context_formatting():
    """Test RAG context formatting."""
    print("\n" + "=" * 60)
    print("Testing RAG Context Formatting")
    print("=" * 60)
    
    pipeline = RetrievalPipeline()
    
    print("\n[1] Retrieving context for summarization...")
    context_data = pipeline.retrieve_context_for_summarization(
        topic="technology",
        max_articles=2,
        max_tokens=500
    )
    
    print(f"   Topic: {context_data['topic']}")
    print(f"   Articles: {context_data['article_count']}")
    
    if context_data['context']:
        print("\n[2] Sample context (first 300 chars):")
        print("   " + "-" * 56)
        sample = context_data['context'][:300].replace('\n', '\n   ')
        print(f"   {sample}...")
        print("   " + "-" * 56)
        print("   ✅ Context formatted correctly")
    else:
        print("\n[2] No context generated")
    
    print("\n[3] Source attribution:")
    for i, source in enumerate(context_data['sources'], 1):
        print(f"   {i}. {source['title'][:40]}...")
        print(f"      URL: {source['url'][:50]}...")
        print(f"      Similarity: {source['similarity']:.4f}")
    
    print("\n✅ RAG context formatting test completed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI News Summarizer - Phase 4 Testing")
    print("Retrieval Module (RAG)")
    print("=" * 60)
    
    results = {
        'vector_store': False,
        'pipeline': False,
        'rag_context': False
    }
    
    # Test 1: Vector Store
    try:
        results['vector_store'] = test_vector_store()
    except Exception as e:
        print(f"\n❌ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Retrieval Pipeline
    try:
        results['pipeline'] = test_retrieval_pipeline()
    except Exception as e:
        print(f"\n❌ Retrieval pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: RAG Context
    try:
        results['rag_context'] = test_rag_context_formatting()
    except Exception as e:
        print(f"\n❌ RAG context test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"ChromaDB Vector Store:   {'✅ PASS' if results['vector_store'] else '❌ FAIL'}")
    print(f"Retrieval Pipeline:      {'✅ PASS' if results['pipeline'] else '❌ FAIL'}")
    print(f"RAG Context Formatting:  {'✅ PASS' if results['rag_context'] else '❌ FAIL'}")
    
    if all(results.values()):
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Phase 4 is complete!")
        print("Ready for Phase 5: LLM Summarization")
        print("=" * 60)
    elif not results['pipeline']:
        print("\n" + "=" * 60)
        print("⚠️  Note: Make sure you have articles in the database")
        print("Run: python test_ingestion.py")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
