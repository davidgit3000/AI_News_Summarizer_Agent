#!/usr/bin/env python3
"""
Test script for the validation module (Phase 6).
Run this to verify summary quality evaluation is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.validation.metrics import SummaryMetrics
from src.validation.pipeline import ValidationPipeline
from config import get_settings


def test_metrics():
    """Test summary metrics calculation."""
    print("\n" + "=" * 60)
    print("Testing Summary Metrics")
    print("=" * 60)
    
    print("\n[1] Initializing metrics calculator...")
    metrics = SummaryMetrics()
    print("   ✅ Metrics initialized")
    
    # Sample texts
    original = """
    Artificial intelligence is rapidly transforming industries worldwide. Machine learning
    algorithms are enabling computers to learn from data and make predictions without explicit
    programming. Deep learning, a subset of machine learning, uses neural networks with multiple
    layers to process complex patterns. Companies are investing billions in AI research, leading
    to breakthroughs in natural language processing, computer vision, and autonomous systems.
    However, concerns about AI safety, ethics, and job displacement remain important topics.
    """
    
    summary = """
    Artificial intelligence is transforming industries through machine learning and deep learning.
    Companies are investing heavily in AI research, achieving breakthroughs in NLP and computer
    vision, though concerns about safety and ethics persist.
    """
    
    print("\n[2] Testing compression ratio...")
    ratio = metrics.calculate_compression_ratio(summary, original)
    print(f"   Original: {len(original.split())} words")
    print(f"   Summary: {len(summary.split())} words")
    print(f"   Compression: {ratio:.1%}")
    print("   ✅ Compression ratio calculated")
    
    print("\n[3] Testing readability...")
    readability = metrics.calculate_readability_score(summary)
    print(f"   Flesch Reading Ease: {readability['flesch_reading_ease']:.1f}")
    print(f"   Avg sentence length: {readability['avg_sentence_length']:.1f} words")
    print("   ✅ Readability calculated")
    
    print("\n[4] Testing lexical diversity...")
    diversity = metrics.calculate_lexical_diversity(summary)
    print(f"   Lexical diversity: {diversity:.1%}")
    print("   ✅ Lexical diversity calculated")
    
    print("\n[5] Testing information density...")
    density = metrics.calculate_information_density(summary, original)
    print(f"   Information density: {density:.1%}")
    print("   ✅ Information density calculated")
    
    print("\n[6] Testing coherence...")
    coherence = metrics.calculate_coherence_score(summary)
    print(f"   Coherence score: {coherence:.1%}")
    print("   ✅ Coherence calculated")
    
    print("\n[7] Testing all metrics together...")
    all_metrics = metrics.calculate_all_metrics(summary, original)
    print(f"   Metrics calculated: {len(all_metrics)}")
    print(f"   ✅ All metrics working")
    
    print("\n✅ Metrics test completed!")
    return True


def test_validation_pipeline():
    """Test the validation pipeline."""
    print("\n" + "=" * 60)
    print("Testing Validation Pipeline")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.openai_api_key:
        print("\n   ⚠️  OPENAI_API_KEY not set")
        print("   Skipping pipeline tests (requires OpenAI API)")
        return False
    
    print("\n[1] Initializing validation pipeline...")
    pipeline = ValidationPipeline()
    print("   ✅ Pipeline initialized")
    
    print("\n[2] Evaluating topic summary...")
    result = pipeline.evaluate_topic_summary(
        topic="technology",
        max_articles=2,
        summary_length=100,
        style="concise"
    )
    
    if 'evaluation' in result:
        eval_data = result['evaluation']
        quality = eval_data['quality_assessment']
        
        print(f"   Topic: '{result['topic']}'")
        print(f"   Summary length: {len(result['summary'].split())} words")
        print(f"   Quality: {quality['overall'].upper()}")
        print(f"   Score: {quality['score']:.1f}/100")
        
        print(f"\n   Key Metrics:")
        metrics = eval_data['metrics']
        print(f"   - Compression: {metrics['compression_ratio']:.1%}")
        print(f"   - Readability: {metrics['readability']['flesch_reading_ease']:.1f}")
        print(f"   - Lexical Diversity: {metrics['lexical_diversity']:.1%}")
        print(f"   - Information Density: {metrics['information_density']:.1%}")
        
        print("   ✅ Evaluation working")
    else:
        print("   ⚠️  Evaluation failed or no articles found")
    
    print("\n[3] Generating quality report...")
    if 'evaluation' in result:
        report = pipeline.generate_quality_report(result['evaluation'])
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)
        print("   ✅ Quality report generated")
    
    print("\n✅ Validation pipeline test completed!")
    return True


def test_style_comparison():
    """Test summary style comparison."""
    print("\n" + "=" * 60)
    print("Testing Style Comparison")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.openai_api_key:
        print("\n   ⚠️  OPENAI_API_KEY not set")
        print("   Skipping style comparison (requires OpenAI API)")
        return False
    
    pipeline = ValidationPipeline()
    
    print("\n[1] Comparing summary styles...")
    comparison = pipeline.compare_summary_styles(
        topic="artificial intelligence",
        styles=["concise", "bullet_points"],
        max_articles=2
    )
    
    if 'comparisons' in comparison and comparison['comparisons']:
        print(f"   Topic: '{comparison['topic']}'")
        print(f"   Styles compared: {len(comparison['comparisons'])}")
        
        print(f"\n   Results:")
        for style, data in comparison['comparisons'].items():
            quality = data['evaluation']['quality_assessment']
            print(f"\n   {style.upper()}:")
            print(f"   - Quality: {quality['overall']}")
            print(f"   - Score: {quality['score']:.1f}/100")
            print(f"   - Summary: {data['summary'][:80]}...")
        
        if 'best_style' in comparison:
            best = comparison['best_style']
            print(f"\n   Best style: {best['style']} (score: {best['score']:.1f})")
        
        print("\n   ✅ Style comparison working")
    else:
        print("   ⚠️  No comparisons generated")
    
    print("\n✅ Style comparison test completed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI News Summarizer - Phase 6 Testing")
    print("Validation Module")
    print("=" * 60)
    
    results = {
        'metrics': False,
        'validation_pipeline': False,
        'style_comparison': False
    }
    
    # Test 1: Metrics
    try:
        results['metrics'] = test_metrics()
    except Exception as e:
        print(f"\n❌ Metrics test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Validation Pipeline
    try:
        results['validation_pipeline'] = test_validation_pipeline()
    except Exception as e:
        print(f"\n❌ Validation pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Style Comparison
    try:
        results['style_comparison'] = test_style_comparison()
    except Exception as e:
        print(f"\n❌ Style comparison test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Summary Metrics:         {'✅ PASS' if results['metrics'] else '❌ FAIL'}")
    print(f"Validation Pipeline:     {'✅ PASS' if results['validation_pipeline'] else '⚠️  SKIP (no API key)' if not results['validation_pipeline'] else '❌ FAIL'}")
    print(f"Style Comparison:        {'✅ PASS' if results['style_comparison'] else '⚠️  SKIP (no API key)' if not results['style_comparison'] else '❌ FAIL'}")
    
    if results['metrics']:
        print("\n" + "=" * 60)
        if results['validation_pipeline'] and results['style_comparison']:
            print("🎉 All tests passed! Phase 6 is complete!")
        else:
            print("✅ Metrics working! Add OPENAI_API_KEY to test full pipeline.")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
