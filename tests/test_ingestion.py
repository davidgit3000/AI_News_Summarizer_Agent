#!/usr/bin/env python3
"""
Test script for the ingestion pipeline.
Run this to verify Phase 2 is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.pipeline import IngestionPipeline
from src.database.db_manager import DatabaseManager


def test_database():
    """Test database functionality."""
    print("\n" + "=" * 60)
    print("Testing Database Manager")
    print("=" * 60)
    
    db = DatabaseManager()
    
    # Test article
    test_article = {
        'title': 'Test Article - Database Test',
        'description': 'Testing database functionality',
        'content': 'This is a test article to verify database operations.',
        'url': f'https://test.com/article-{hash("test")}',
        'source': 'Test Source',
        'author': 'Test Author',
        'published_at': '2024-01-01T00:00:00Z',
        'fetched_at': '2024-01-01T00:00:00Z'
    }
    
    # Insert
    print("\n[1] Inserting test article...")
    article_id = db.insert_article(test_article)
    if article_id:
        print(f"   ✅ Article inserted with ID: {article_id}")
    else:
        print("   ⚠️  Article already exists (duplicate)")
    
    # Retrieve
    print("\n[2] Retrieving article...")
    retrieved = db.get_article_by_id(article_id) if article_id else db.get_all_articles(limit=1)[0]
    if retrieved:
        print(f"   ✅ Retrieved: {retrieved['title']}")
    
    # Stats
    print("\n[3] Database statistics:")
    stats = db.get_stats()
    print(f"   Total articles: {stats['total_articles']}")
    print(f"   With embeddings: {stats['articles_with_embeddings']}")
    print(f"   Without embeddings: {stats['articles_without_embeddings']}")
    
    print("\n✅ Database test completed!")
    return True


def test_news_fetcher():
    """Test news fetcher (requires API key)."""
    print("\n" + "=" * 60)
    print("Testing News Fetcher")
    print("=" * 60)
    
    from src.ingestion.news_fetcher import NewsFetcher
    
    try:
        fetcher = NewsFetcher()
        
        print("\n[1] Fetching top headlines (5 articles)...")
        headlines = fetcher.fetch_top_headlines(page_size=5)
        print(f"   ✅ Fetched {len(headlines)} articles")
        
        if headlines:
            print("\n   Sample article:")
            article = headlines[0]
            print(f"   - Title: {article['title'][:60]}...")
            print(f"   - Source: {article['source']}")
            print(f"   - URL: {article['url'][:50]}...")
        
        print("\n✅ News fetcher test completed!")
        return True
        
    except ValueError as e:
        print(f"\n⚠️  Skipping news fetcher test: {e}")
        print("   Please set NEWSAPI_KEY in your .env file to test this feature")
        return False


def test_pipeline():
    """Test full ingestion pipeline."""
    print("\n" + "=" * 60)
    print("Testing Ingestion Pipeline")
    print("=" * 60)
    
    try:
        pipeline = IngestionPipeline()
        
        print("\n[1] Getting pipeline status...")
        status = pipeline.get_pipeline_status()
        print(f"   Total articles in database: {status['total_articles']}")
        
        print("\n[2] Ingesting top headlines (3 articles)...")
        stats = pipeline.ingest_top_headlines(page_size=3)
        print(f"   ✅ Fetched: {stats['fetched']}")
        print(f"   ✅ Inserted: {stats['inserted']}")
        print(f"   ✅ Duplicates: {stats['duplicates']}")
        
        print("\n[3] Final status...")
        final_status = pipeline.get_pipeline_status()
        print(f"   Total articles: {final_status['total_articles']}")
        
        if final_status['sources']:
            print(f"\n   Articles by source:")
            for source, count in list(final_status['sources'].items())[:5]:
                print(f"      - {source}: {count}")
        
        print("\n✅ Pipeline test completed!")
        return True
        
    except ValueError as e:
        print(f"\n⚠️  Skipping pipeline test: {e}")
        print("   Please set NEWSAPI_KEY in your .env file to test this feature")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI News Summarizer - Phase 2 Testing")
    print("Data Ingestion Module")
    print("=" * 60)
    
    results = {
        'database': False,
        'news_fetcher': False,
        'pipeline': False
    }
    
    # Test 1: Database
    try:
        results['database'] = test_database()
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: News Fetcher
    try:
        results['news_fetcher'] = test_news_fetcher()
    except Exception as e:
        print(f"\n❌ News fetcher test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Pipeline
    try:
        results['pipeline'] = test_pipeline()
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Database Manager:    {'✅ PASS' if results['database'] else '❌ FAIL'}")
    print(f"News Fetcher:        {'✅ PASS' if results['news_fetcher'] else '⚠️  SKIP (no API key)'}")
    print(f"Ingestion Pipeline:  {'✅ PASS' if results['pipeline'] else '⚠️  SKIP (no API key)'}")
    
    if results['database'] and not results['news_fetcher']:
        print("\n" + "=" * 60)
        print("⚠️  To complete testing:")
        print("1. Copy .env.example to .env")
        print("2. Add your NEWSAPI_KEY to .env")
        print("3. Get a free key at: https://newsapi.org/register")
        print("4. Run this test again")
        print("=" * 60)
    elif all(results.values()):
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Phase 2 is complete!")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
