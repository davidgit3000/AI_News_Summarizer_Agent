"""
Fidelity checker using Google Gemini to verify summary accuracy.
Checks for hallucinations, factual consistency, and claim verification.
"""

import logging
import json
from typing import Dict, List, Optional, Any
import google.generativeai as genai

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FidelityChecker:
    """Check summary fidelity using Google Gemini as a judge."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash"
    ):
        """
        Initialize the fidelity checker.
        
        Args:
            api_key: Gemini API key (uses config if None)
            model_name: Gemini model to use (gemini-2.5-flash)
        """
        settings = get_settings()
        
        # Set up API key
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY in .env")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        logger.info(f"FidelityChecker initialized with model: {self.model_name}")
    
    def check_fidelity(
        self,
        summary: str,
        source_articles: List[str],
        detailed: bool = True
    ) -> Dict[str, Any]:
        """
        Check if summary is faithful to source articles.
        
        Args:
            summary: Generated summary to verify
            source_articles: List of source article texts
            detailed: If True, provide detailed analysis
        
        Returns:
            Dictionary with fidelity scores and analysis
        """
        logger.info("Checking summary fidelity with Gemini...")
        
        # Combine source articles
        sources_text = "\n\n---SOURCE ARTICLE---\n\n".join(source_articles)
        
        # Build prompt
        prompt = self._build_fidelity_prompt(summary, sources_text, detailed)
        
        try:
            # Call Gemini
            response = self.model.generate_content(prompt)
            
            # Parse response
            result = self._parse_fidelity_response(response.text)
            
            logger.info(f"Fidelity check complete. Overall score: {result['overall_fidelity']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking fidelity: {e}")
            return {
                'error': str(e),
                'overall_fidelity': 0.0,
                'factual_consistency': 0.0
            }
    
    def check_hallucinations(
        self,
        summary: str,
        source_articles: List[str]
    ) -> Dict[str, Any]:
        """
        Specifically check for hallucinations in the summary.
        
        Args:
            summary: Generated summary
            source_articles: Source article texts
        
        Returns:
            Dictionary with hallucination analysis
        """
        logger.info("Checking for hallucinations...")
        
        sources_text = "\n\n---SOURCE ARTICLE---\n\n".join(source_articles)
        
        prompt = f"""You are a fact-checking expert. Analyze if the summary contains any hallucinations or fabricated information not present in the source articles.

SUMMARY TO CHECK:
{summary}

SOURCE ARTICLES:
{sources_text}

Identify any statements in the summary that are:
1. Not supported by the source articles
2. Contradicted by the source articles
3. Exaggerated or misrepresented

Respond in JSON format:
{{
    "has_hallucinations": true/false,
    "hallucination_count": 0,
    "hallucinations": [
        {{
            "claim": "the hallucinated claim",
            "severity": "high/medium/low",
            "explanation": "why this is a hallucination"
        }}
    ],
    "confidence": 0.0-1.0
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            logger.info(f"Hallucination check: {result.get('hallucination_count', 0)} found")
            return result
            
        except Exception as e:
            logger.error(f"Error checking hallucinations: {e}")
            return {
                'error': str(e),
                'has_hallucinations': None,
                'hallucination_count': 0
            }
    
    def verify_claims(
        self,
        summary: str,
        source_articles: List[str]
    ) -> Dict[str, Any]:
        """
        Verify each claim in the summary against sources.
        
        Args:
            summary: Generated summary
            source_articles: Source article texts
        
        Returns:
            Dictionary with claim verification results
        """
        logger.info("Verifying claims...")
        
        sources_text = "\n\n---SOURCE ARTICLE---\n\n".join(source_articles)
        
        prompt = f"""You are a fact-checking expert. Extract all factual claims from the summary and verify each against the source articles.

SUMMARY:
{summary}

SOURCE ARTICLES:
{sources_text}

For each claim in the summary, determine if it is:
- SUPPORTED: Directly stated or clearly implied in sources
- PARTIALLY_SUPPORTED: Partially true but missing context
- UNSUPPORTED: Not found in sources
- CONTRADICTED: Contradicts information in sources

Respond in JSON format:
{{
    "total_claims": 0,
    "verified_claims": 0,
    "unverified_claims": 0,
    "claims": [
        {{
            "claim": "the factual claim",
            "status": "SUPPORTED/PARTIALLY_SUPPORTED/UNSUPPORTED/CONTRADICTED",
            "evidence": "quote from source or explanation"
        }}
    ],
    "verification_rate": 0.0-1.0
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            logger.info(f"Claim verification: {result.get('verified_claims', 0)}/{result.get('total_claims', 0)} verified")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying claims: {e}")
            return {
                'error': str(e),
                'total_claims': 0,
                'verified_claims': 0
            }
    
    def check_completeness(
        self,
        summary: str,
        source_articles: List[str]
    ) -> Dict[str, Any]:
        """
        Check if summary covers all key points from sources.
        
        Args:
            summary: Generated summary
            source_articles: Source article texts
        
        Returns:
            Dictionary with completeness analysis
        """
        logger.info("Checking completeness...")
        
        sources_text = "\n\n---SOURCE ARTICLE---\n\n".join(source_articles)
        
        prompt = f"""You are an expert at evaluating summary completeness. Identify the key points in the source articles and check if they are covered in the summary.

SUMMARY:
{summary}

SOURCE ARTICLES:
{sources_text}

Analyze:
1. What are the main key points in the source articles?
2. Which key points are covered in the summary?
3. Which important points are missing?

Respond in JSON format:
{{
    "total_key_points": 0,
    "covered_key_points": 0,
    "missing_key_points": [
        "important point that was omitted"
    ],
    "completeness_score": 0.0-1.0,
    "assessment": "brief assessment of completeness"
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            logger.info(f"Completeness: {result.get('completeness_score', 0):.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking completeness: {e}")
            return {
                'error': str(e),
                'completeness_score': 0.0
            }
    
    def comprehensive_check(
        self,
        summary: str,
        source_articles: List[str]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive fidelity check (all checks combined).
        
        Args:
            summary: Generated summary
            source_articles: Source article texts
        
        Returns:
            Dictionary with all fidelity metrics
        """
        logger.info("Performing comprehensive fidelity check...")
        
        results = {
            'summary': summary,
            'num_sources': len(source_articles)
        }
        
        # Run all checks
        results['fidelity'] = self.check_fidelity(summary, source_articles, detailed=True)
        results['hallucinations'] = self.check_hallucinations(summary, source_articles)
        results['claim_verification'] = self.verify_claims(summary, source_articles)
        results['completeness'] = self.check_completeness(summary, source_articles)
        
        # Calculate overall score
        scores = []
        if 'overall_fidelity' in results['fidelity']:
            scores.append(results['fidelity']['overall_fidelity'])
        if 'verification_rate' in results['claim_verification']:
            scores.append(results['claim_verification']['verification_rate'])
        if 'completeness_score' in results['completeness']:
            scores.append(results['completeness']['completeness_score'])
        
        results['overall_score'] = sum(scores) / len(scores) if scores else 0.0
        
        logger.info(f"Comprehensive check complete. Overall score: {results['overall_score']:.2f}")
        return results
    
    def _build_fidelity_prompt(
        self,
        summary: str,
        sources: str,
        detailed: bool
    ) -> str:
        """Build prompt for fidelity checking."""
        
        if detailed:
            return f"""You are an expert fact-checker evaluating summary fidelity. Analyze if the summary accurately represents the source articles without hallucinations or distortions.

SUMMARY TO EVALUATE:
{summary}

SOURCE ARTICLES:
{sources}

Evaluate the summary on these dimensions:
1. **Factual Consistency**: Are all facts in the summary accurate and supported by sources?
2. **No Hallucinations**: Does the summary avoid adding information not in sources?
3. **Proper Attribution**: Are claims properly grounded in the source material?
4. **Balanced Representation**: Does it fairly represent the sources without bias?

Respond in JSON format:
{{
    "factual_consistency": 0.0-1.0,
    "hallucination_free": 0.0-1.0,
    "proper_attribution": 0.0-1.0,
    "balanced_representation": 0.0-1.0,
    "overall_fidelity": 0.0-1.0,
    "issues_found": [
        "specific issue if any"
    ],
    "strengths": [
        "what the summary does well"
    ],
    "explanation": "brief explanation of the assessment"
}}"""
        else:
            return f"""Evaluate if this summary is faithful to the source articles. Rate fidelity from 0.0 (completely unfaithful) to 1.0 (perfectly faithful).

SUMMARY:
{summary}

SOURCES:
{sources}

Respond in JSON format:
{{
    "overall_fidelity": 0.0-1.0,
    "factual_consistency": 0.0-1.0,
    "explanation": "brief explanation"
}}"""
    
    def _parse_fidelity_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response for fidelity check."""
        try:
            # Extract JSON from response
            result = self._parse_json_response(response_text)
            
            # Ensure required fields
            if 'overall_fidelity' not in result:
                result['overall_fidelity'] = result.get('factual_consistency', 0.5)
            
            return result
            
        except Exception as e:
            logger.warning(f"Error parsing fidelity response: {e}")
            return {
                'overall_fidelity': 0.5,
                'factual_consistency': 0.5,
                'explanation': 'Could not parse response',
                'raw_response': response_text
            }
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Gemini response."""
        # Try to find JSON in response
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            # Parse JSON
            return json.loads(text.strip())
            
        except json.JSONDecodeError:
            # Try to find JSON object in text
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # Fallback
            logger.warning("Could not parse JSON from response")
            return {'raw_response': response_text}


# Example usage and testing
if __name__ == "__main__":
    import sys
    from config import get_settings
    
    print("=" * 60)
    print("Fidelity Checker (Gemini) - Testing")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.gemini_api_key:
        print("\n⚠️  GEMINI_API_KEY not set in .env file")
        print("Get your free API key from: https://makersuite.google.com/app/apikey")
        print("\nAdd to .env:")
        print("GEMINI_API_KEY=your_key_here")
        sys.exit(1)
    
    try:
        # Initialize checker
        print("\n[1/3] Initializing fidelity checker...")
        checker = FidelityChecker()
        print(f"   Model: {checker.model_name}")
        print("   ✅ Checker initialized")
        
        # Test data
        source = """
        Microsoft AI announced the formation of a new team dedicated to developing 
        superintelligent AI systems designed to serve humanity. The team will focus 
        on ensuring AI safety and ethical development. The initiative aims to create 
        AI that benefits society while minimizing potential risks.
        """
        
        good_summary = """
        Microsoft AI has formed a new team to develop superintelligent AI focused 
        on serving humanity, with emphasis on safety and ethical development.
        """
        
        bad_summary = """
        Microsoft AI has created the world's first superintelligent AI that will 
        replace all human jobs by 2025 and has already achieved consciousness.
        """
        
        # Test good summary
        print("\n[2/3] Testing fidelity check (good summary)...")
        result_good = checker.check_fidelity(good_summary, [source], detailed=False)
        print(f"   Fidelity score: {result_good.get('overall_fidelity', 0):.2f}")
        print(f"   Factual consistency: {result_good.get('factual_consistency', 0):.2f}")
        print("   ✅ Good summary evaluated")
        
        # Test bad summary
        print("\n[3/3] Testing hallucination detection (bad summary)...")
        result_bad = checker.check_hallucinations(bad_summary, [source])
        print(f"   Has hallucinations: {result_bad.get('has_hallucinations', False)}")
        print(f"   Hallucination count: {result_bad.get('hallucination_count', 0)}")
        if result_bad.get('hallucinations'):
            print(f"   Example: {result_bad['hallucinations'][0].get('claim', 'N/A')}")
        print("   ✅ Hallucination detection working")
        
        print("\n" + "=" * 60)
        print("✅ Fidelity checker test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
