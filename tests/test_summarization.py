#!/usr/bin/env python3
"""
Test script for the summarization module (Phase 5).
Run this to verify RAG-based summarization is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.summarization.llm_client import LLMClient
from src.summarization.pipeline import SummarizationPipeline
from config import get_settings


def test_llm_client():
    """Test the LLM client."""
    print("\n" + "=" * 60)
    print("Testing LLM Client")
    print("=" * 60)
    
    print("\n[1] Initializing LLM client...")
    client = LLMClient()
    
    info = client.get_model_info()
    print(f"   Model: {info['model']}")
    print(f"   Temperature: {info['temperature']}")
    print(f"   Max tokens: {info['max_tokens']}")
    print("   ✅ Client initialized")
    
    print("\n[2] Testing basic text generation...")
    prompt = "What is machine learning in one sentence?"
    response = client.generate(prompt)
    print(f"   Prompt: {prompt}")
    print(f"   Response: {response[:100]}...")
    print("   ✅ Generation working")
    
    print("\n[3] Testing summarization...")
    sample_text = """
    Artificial intelligence is rapidly transforming industries worldwide. Machine learning
    algorithms are enabling computers to learn from data and make predictions. Deep learning,
    using neural networks, has achieved remarkable results in image recognition and natural
    language processing. Companies are investing heavily in AI research, leading to innovations
    in autonomous vehicles, healthcare diagnostics, and personalized recommendations.
    """
    
    summary = client.summarize(sample_text, max_length=30, style="concise")
    print(f"   Original: {len(sample_text.split())} words")
    print(f"   Summary: {summary}")
    print(f"   Summary length: {len(summary.split())} words")
    print("   ✅ Summarization working")
    
    print("\n[4] Testing key point extraction...")
    key_points = client.extract_key_points(sample_text, num_points=3)
    print(f"   Extracted {len(key_points)} key points:")
    for i, point in enumerate(key_points, 1):
        print(f"   {i}. {point[:60]}...")
    print("   ✅ Key point extraction working")
    
    print("\n✅ LLM client test completed!")
    return True


def test_rag_summarization():
    """Test RAG-based summarization pipeline."""
    print("\n" + "=" * 60)
    print("Testing RAG Summarization Pipeline")
    print("=" * 60)
    
    print("\n[1] Initializing summarization pipeline...")
    pipeline = SummarizationPipeline()
    print("   ✅ Pipeline initialized")
    
    print("\n[2] Testing topic summarization (concise)...")
    topic = "technology"
    result = pipeline.summarize_topic(
        topic=topic,
        max_articles=2,
        summary_length=100,
        style="concise"
    )
    
    print(f"   Topic: '{result['topic']}'")
    print(f"   Articles used: {result['article_count']}")
    print(f"   Summary length: {len(result['summary'].split())} words")
    print(f"\n   Summary:")
    print(f"   {'-' * 56}")
    print(f"   {result['summary']}")
    print(f"   {'-' * 56}")
    
    if result['sources']:
        print(f"\n   Sources ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'], 1):
            title = source['title'][:50] + "..." if len(source['title']) > 50 else source['title']
            print(f"   {i}. {title}")
            print(f"      Source: {source['source']}, Similarity: {source['similarity']:.4f}")
    
    print("\n   ✅ Topic summarization working")
    
    print("\n[3] Testing bullet point style...")
    result_bullets = pipeline.summarize_topic(
        topic="artificial intelligence",
        max_articles=2,
        summary_length=80,
        style="bullet_points"
    )
    
    print(f"   Topic: '{result_bullets['topic']}'")
    print(f"   Summary (bullet points):")
    print(f"   {'-' * 56}")
    print(f"   {result_bullets['summary']}")
    print(f"   {'-' * 56}")
    print("   ✅ Bullet point style working")
    
    print("\n[4] Testing headline generation...")
    headline = pipeline.generate_headline(topic="technology", max_articles=2)
    print(f"   Generated headline: '{headline}'")
    print("   ✅ Headline generation working")
    
    print("\n[5] Testing key insights extraction...")
    insights_result = pipeline.extract_key_insights(
        topic="technology",
        num_insights=3,
        max_articles=2
    )
    
    print(f"   Topic: '{insights_result['topic']}'")
    print(f"   Insights extracted: {len(insights_result['insights'])}")
    for i, insight in enumerate(insights_result['insights'], 1):
        print(f"   {i}. {insight[:70]}...")
    print("   ✅ Key insights extraction working")
    
    print("\n✅ RAG summarization pipeline test completed!")
    return True


def test_advanced_features():
    """Test advanced summarization features."""
    print("\n" + "=" * 60)
    print("Testing Advanced Features")
    print("=" * 60)
    
    pipeline = SummarizationPipeline()
    
    print("\n[1] Testing question answering...")
    questions = [
        "What are the main developments?",
        "What are the key challenges?"
    ]
    
    result = pipeline.summarize_with_questions(
        topic="artificial intelligence",
        questions=questions,
        max_articles=2
    )
    
    print(f"   Topic: '{result['topic']}'")
    print(f"   Articles analyzed: {result['article_count']}")
    print(f"\n   Summary:")
    print(f"   {result['summary'][:150]}...")
    
    print(f"\n   Answers to questions:")
    for question, answer in result['answers'].items():
        print(f"\n   Q: {question}")
        print(f"   A: {answer[:100]}...")
    
    print("\n   ✅ Question answering working")
    
    print("\n✅ Advanced features test completed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI News Summarizer - Phase 5 Testing")
    print("LLM Summarization Module (RAG)")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.openai_api_key:
        print("\n" + "=" * 60)
        print("⚠️  OPENAI_API_KEY not set")
        print("=" * 60)
        print("\nTo test Phase 5, you need to:")
        print("1. Get an OpenAI API key from https://platform.openai.com")
        print("2. Add it to your .env file:")
        print("   OPENAI_API_KEY=your-key-here")
        print("\nSkipping Phase 5 tests for now.")
        print("=" * 60)
        return
    
    results = {
        'llm_client': False,
        'rag_summarization': False,
        'advanced_features': False
    }
    
    # Test 1: LLM Client
    try:
        results['llm_client'] = test_llm_client()
    except Exception as e:
        print(f"\n❌ LLM client test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: RAG Summarization
    try:
        results['rag_summarization'] = test_rag_summarization()
    except Exception as e:
        print(f"\n❌ RAG summarization test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Advanced Features
    try:
        results['advanced_features'] = test_advanced_features()
    except Exception as e:
        print(f"\n❌ Advanced features test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"LLM Client:              {'✅ PASS' if results['llm_client'] else '❌ FAIL'}")
    print(f"RAG Summarization:       {'✅ PASS' if results['rag_summarization'] else '❌ FAIL'}")
    print(f"Advanced Features:       {'✅ PASS' if results['advanced_features'] else '❌ FAIL'}")
    
    if all(results.values()):
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Phase 5 is complete!")
        print("Ready for Phase 6: Validation Module")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
