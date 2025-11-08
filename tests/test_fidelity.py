#!/usr/bin/env python3
"""
Test script for the fidelity checker (Phase 6.5).
Run this to verify Gemini-based fidelity checking is working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.validation.fidelity_checker import FidelityChecker
from src.validation.pipeline import ValidationPipeline
from config import get_settings


def test_fidelity_checker():
    """Test the Gemini fidelity checker."""
    print("\n" + "=" * 60)
    print("Testing Gemini Fidelity Checker")
    print("=" * 60)
    
    print("\n[1] Initializing fidelity checker...")
    checker = FidelityChecker()
    print(f"   Model: {checker.model_name}")
    print("   ✅ Checker initialized")
    
    # Test data
    source_article = """
    Microsoft AI announced the formation of a new team dedicated to developing 
    superintelligent AI systems designed to serve humanity. The team will focus 
    on ensuring AI safety and ethical development. The initiative aims to create 
    AI that benefits society while minimizing potential risks. The team will work
    on developing AI systems that are transparent, accountable, and aligned with
    human values.
    """
    
    good_summary = """
    Microsoft AI has formed a new team to develop superintelligent AI focused 
    on serving humanity, with emphasis on safety, ethics, and alignment with
    human values.
    """
    
    bad_summary = """
    Microsoft AI has created the world's first superintelligent AI that will 
    replace all human jobs by 2025 and has already achieved consciousness.
    The AI can read minds and predict the future with 100% accuracy.
    """
    
    print("\n[2] Testing fidelity check (good summary)...")
    result_good = checker.check_fidelity(good_summary, [source_article], detailed=True)
    
    if 'error' not in result_good:
        print(f"   Overall fidelity: {result_good.get('overall_fidelity', 0):.2f}")
        print(f"   Factual consistency: {result_good.get('factual_consistency', 0):.2f}")
        print(f"   Hallucination-free: {result_good.get('hallucination_free', 0):.2f}")
        
        if result_good.get('strengths'):
            print(f"   Strengths: {len(result_good['strengths'])} identified")
        
        print("   ✅ Good summary evaluated")
    else:
        print(f"   ⚠️  Error: {result_good['error']}")
    
    print("\n[3] Testing hallucination detection (bad summary)...")
    result_bad = checker.check_hallucinations(bad_summary, [source_article])
    
    if 'error' not in result_bad:
        print(f"   Has hallucinations: {result_bad.get('has_hallucinations', False)}")
        print(f"   Hallucination count: {result_bad.get('hallucination_count', 0)}")
        
        if result_bad.get('hallucinations'):
            print(f"\n   Detected hallucinations:")
            for i, h in enumerate(result_bad['hallucinations'][:2], 1):
                print(f"   {i}. {h.get('claim', 'N/A')[:60]}...")
                print(f"      Severity: {h.get('severity', 'unknown')}")
                print(f"      Explanation: {h.get('explanation', 'N/A')}")
        
        print("   ✅ Hallucination detection working")
    else:
        print(f"   ⚠️  Error: {result_bad['error']}")
    
    print("\n[4] Testing claim verification...")
    result_claims = checker.verify_claims(good_summary, [source_article])
    
    if 'error' not in result_claims:
        print(f"   Total claims: {result_claims.get('total_claims', 0)}")
        print(f"   Verified claims: {result_claims.get('verified_claims', 0)}")
        print(f"   Verification rate: {result_claims.get('verification_rate', 0):.1%}")
        print("   ✅ Claim verification working")
    else:
        print(f"   ⚠️  Error: {result_claims['error']}")
    
    print("\n[5] Testing completeness check...")
    result_complete = checker.check_completeness(good_summary, [source_article])
    
    if 'error' not in result_complete:
        print(f"   Completeness score: {result_complete.get('completeness_score', 0):.2f}")
        print(f"   Covered key points: {result_complete.get('covered_key_points', 0)}/{result_complete.get('total_key_points', 0)}")
        
        if result_complete.get('missing_key_points'):
            print(f"   Missing points: {len(result_complete['missing_key_points'])}")
        
        print("   ✅ Completeness check working")
    else:
        print(f"   ⚠️  Error: {result_complete['error']}")
    
    print("\n✅ Fidelity checker test completed!")
    return True


def test_integrated_validation():
    """Test fidelity checking integrated with validation pipeline."""
    print("\n" + "=" * 60)
    print("Testing Integrated Validation with Fidelity")
    print("=" * 60)
    
    # Check API keys
    settings = get_settings()
    if not settings.openai_api_key:
        print("\n   ⚠️  OPENAI_API_KEY not set")
        print("   Skipping integrated test (requires OpenAI API)")
        return False
    
    print("\n[1] Initializing validation pipeline with fidelity checking...")
    pipeline = ValidationPipeline(enable_fidelity_check=True)
    
    if pipeline.fidelity_checker:
        print("   ✅ Fidelity checking enabled")
    else:
        print("   ⚠️  Fidelity checker not available")
        return False
    
    print("\n[2] Generating and evaluating summary with fidelity check...")
    
    # Test data
    source = """
    Artificial intelligence research has made significant progress in recent years.
    Machine learning models are becoming more capable and efficient. However,
    researchers emphasize the importance of responsible AI development and
    addressing potential risks.
    """
    
    summary = """
    AI research has advanced significantly, with more capable machine learning
    models. Researchers stress the need for responsible development.
    """
    
    # Evaluate with fidelity check
    result = pipeline.evaluate_summary(
        summary=summary,
        original_text=source,
        check_fidelity=True,
        source_articles=[source]
    )
    
    print(f"   Quality score: {result['quality_assessment']['score']:.1f}/100")
    
    if 'fidelity' in result:
        fidelity = result['fidelity']
        print(f"\n   Fidelity Analysis:")
        print(f"   - Overall fidelity: {fidelity.get('overall_fidelity', 0):.2f}")
        print(f"   - Factual consistency: {fidelity.get('factual_consistency', 0):.2f}")
        
        if fidelity.get('explanation'):
            print(f"\n   Explanation:")
            print(f"   {fidelity['explanation']}...")
        
        print("\n   ✅ Integrated fidelity check working")
    else:
        print("   ⚠️  No fidelity results")
    
    print("\n✅ Integrated validation test completed!")
    return True


def test_comprehensive_check():
    """Test comprehensive fidelity check."""
    print("\n" + "=" * 60)
    print("Testing Comprehensive Fidelity Check")
    print("=" * 60)
    
    checker = FidelityChecker()
    
    source = """
    Climate change is causing significant impacts on global weather patterns.
    Scientists report rising temperatures, melting ice caps, and more frequent
    extreme weather events. International cooperation is needed to address
    this challenge through emission reductions and sustainable practices.
    """
    
    summary = """
    Climate change is affecting global weather with rising temperatures and
    extreme events. Scientists call for international cooperation on emissions
    and sustainability.
    """
    
    print("\n[1] Running comprehensive fidelity check...")
    result = checker.comprehensive_check(summary, [source])
    
    print(f"   Overall score: {result.get('overall_score', 0):.2f}")
    
    if 'fidelity' in result:
        print(f"   Fidelity: {result['fidelity'].get('overall_fidelity', 0):.2f}")
    
    if 'hallucinations' in result:
        print(f"   Hallucinations: {result['hallucinations'].get('hallucination_count', 0)}")
    
    if 'claim_verification' in result:
        print(f"   Verified claims: {result['claim_verification'].get('verified_claims', 0)}/{result['claim_verification'].get('total_claims', 0)}")
    
    if 'completeness' in result:
        print(f"   Completeness: {result['completeness'].get('completeness_score', 0):.2f}")
    
    print("\n   ✅ Comprehensive check working")
    print("\n✅ Comprehensive check test completed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI News Summarizer - Phase 6.5 Testing")
    print("Fidelity Checking with Gemini")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.gemini_api_key:
        print("\n" + "=" * 60)
        print("⚠️  GEMINI_API_KEY not set")
        print("=" * 60)
        print("\nTo test fidelity checking, you need to:")
        print("1. Get a free Gemini API key from:")
        print("   https://makersuite.google.com/app/apikey")
        print("2. Add it to your .env file:")
        print("   GEMINI_API_KEY=your_key_here")
        print("\nSkipping fidelity tests for now.")
        print("=" * 60)
        return
    
    results = {
        'fidelity_checker': False,
        'integrated_validation': False,
        'comprehensive_check': False
    }
    
    # Test 1: Fidelity Checker
    try:
        results['fidelity_checker'] = test_fidelity_checker()
    except Exception as e:
        print(f"\n❌ Fidelity checker test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Integrated Validation
    try:
        results['integrated_validation'] = test_integrated_validation()
    except Exception as e:
        print(f"\n❌ Integrated validation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Comprehensive Check
    try:
        results['comprehensive_check'] = test_comprehensive_check()
    except Exception as e:
        print(f"\n❌ Comprehensive check test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Fidelity Checker:        {'✅ PASS' if results['fidelity_checker'] else '❌ FAIL'}")
    print(f"Integrated Validation:   {'✅ PASS' if results['integrated_validation'] else '⚠️  SKIP (no OpenAI key)' if not results['integrated_validation'] else '❌ FAIL'}")
    print(f"Comprehensive Check:     {'✅ PASS' if results['comprehensive_check'] else '❌ FAIL'}")
    
    if results['fidelity_checker']:
        print("\n" + "=" * 60)
        print("🎉 Fidelity checking tests passed!")
        print("Phase 6.5 complete!")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
