"""
Validation pipeline for evaluating and comparing summaries.
Integrates metrics calculation with summarization pipeline.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.validation.metrics import SummaryMetrics
from src.validation.fidelity_checker import FidelityChecker
from src.summarization.pipeline import SummarizationPipeline
from src.retrieval.pipeline import RetrievalPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationPipeline:
    """Pipeline for validating and evaluating summaries."""
    
    def __init__(
        self,
        summarization_pipeline: Optional[SummarizationPipeline] = None,
        enable_fidelity_check: bool = False
    ):
        """
        Initialize the validation pipeline.
        
        Args:
            summarization_pipeline: Existing summarization pipeline (optional)
            enable_fidelity_check: Enable Gemini-based fidelity checking (optional)
        """
        self.metrics = SummaryMetrics()
        self.summarization_pipeline = summarization_pipeline or SummarizationPipeline()
        
        # Initialize fidelity checker if enabled
        self.fidelity_checker = None
        if enable_fidelity_check:
            try:
                self.fidelity_checker = FidelityChecker()
                logger.info("Fidelity checking enabled (Gemini)")
            except Exception as e:
                logger.warning(f"Could not initialize fidelity checker: {e}")
        
        logger.info("ValidationPipeline initialized successfully")
    
    def evaluate_summary(
        self,
        summary: str,
        original_text: str,
        reference_summary: Optional[str] = None,
        check_fidelity: bool = False,
        source_articles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a summary against the original text.
        
        Args:
            summary: Generated summary
            original_text: Original text
            reference_summary: Reference summary for ROUGE (optional)
            check_fidelity: Run fidelity check with Gemini (optional)
            source_articles: Source articles for fidelity check (optional)
        
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating summary...")
        
        # Calculate all metrics
        metrics = self.metrics.calculate_all_metrics(
            summary=summary,
            original=original_text,
            reference=reference_summary
        )
        
        # Add quality assessment
        quality = self._assess_quality(metrics)
        
        result = {
            'metrics': metrics,
            'quality_assessment': quality,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add fidelity check if requested and available
        if check_fidelity and self.fidelity_checker and source_articles:
            logger.info("Running fidelity check...")
            fidelity_result = self.fidelity_checker.check_fidelity(
                summary=summary,
                source_articles=source_articles,
                detailed=True
            )
            result['fidelity'] = fidelity_result
        
        logger.info(f"Summary evaluation complete. Quality: {quality['overall']}")
        return result
    
    def evaluate_topic_summary(
        self,
        topic: str,
        max_articles: int = 5,
        summary_length: int = 200,
        style: str = "concise"
    ) -> Dict[str, Any]:
        """
        Generate and evaluate a topic summary.
        
        Args:
            topic: Topic to summarize
            max_articles: Maximum articles to use
            summary_length: Target summary length
            style: Summary style
        
        Returns:
            Dictionary with summary and evaluation
        """
        logger.info(f"Generating and evaluating summary for: {topic}")
        
        # Generate summary
        summary_result = self.summarization_pipeline.summarize_topic(
            topic=topic,
            max_articles=max_articles,
            summary_length=summary_length,
            style=style
        )
        
        if not summary_result['summary'] or summary_result['article_count'] == 0:
            return {
                'topic': topic,
                'summary': summary_result['summary'],
                'evaluation': None,
                'error': 'No articles found or summary generation failed'
            }
        
        # Get original articles for evaluation
        retrieval_pipeline = self.summarization_pipeline.retrieval_pipeline
        context_data = retrieval_pipeline.retrieve_context_for_summarization(
            topic=topic,
            max_articles=max_articles
        )
        
        # Evaluate summary
        evaluation = self.evaluate_summary(
            summary=summary_result['summary'],
            original_text=context_data['context']
        )
        
        return {
            'topic': topic,
            'summary': summary_result['summary'],
            'sources': summary_result['sources'],
            'article_count': summary_result['article_count'],
            'evaluation': evaluation,
            'timestamp': datetime.now().isoformat()
        }
    
    def compare_summary_styles(
        self,
        topic: str,
        styles: List[str] = None,
        max_articles: int = 5
    ) -> Dict[str, Any]:
        """
        Compare different summary styles for the same topic.
        
        Args:
            topic: Topic to summarize
            styles: List of styles to compare
            max_articles: Maximum articles to use
        
        Returns:
            Dictionary with comparison results
        """
        if styles is None:
            styles = ["concise", "comprehensive", "bullet_points"]
        
        logger.info(f"Comparing {len(styles)} summary styles for: {topic}")
        
        # Get original context once
        retrieval_pipeline = self.summarization_pipeline.retrieval_pipeline
        context_data = retrieval_pipeline.retrieve_context_for_summarization(
            topic=topic,
            max_articles=max_articles
        )
        
        if not context_data['context']:
            return {
                'topic': topic,
                'error': 'No articles found',
                'comparisons': {}
            }
        
        # Generate and evaluate each style
        comparisons = {}
        for style in styles:
            logger.info(f"Generating {style} summary...")
            
            summary_result = self.summarization_pipeline.summarize_topic(
                topic=topic,
                max_articles=max_articles,
                summary_length=150,
                style=style
            )
            
            evaluation = self.evaluate_summary(
                summary=summary_result['summary'],
                original_text=context_data['context']
            )
            
            comparisons[style] = {
                'summary': summary_result['summary'],
                'evaluation': evaluation
            }
        
        # Determine best style
        best_style = self._determine_best_style(comparisons)
        
        return {
            'topic': topic,
            'comparisons': comparisons,
            'best_style': best_style,
            'article_count': context_data['article_count'],
            'timestamp': datetime.now().isoformat()
        }
    
    def batch_evaluate(
        self,
        topics: List[str],
        max_articles: int = 5
    ) -> Dict[str, Any]:
        """
        Evaluate summaries for multiple topics.
        
        Args:
            topics: List of topics to evaluate
            max_articles: Maximum articles per topic
        
        Returns:
            Dictionary with batch evaluation results
        """
        logger.info(f"Batch evaluating {len(topics)} topics...")
        
        results = []
        for topic in topics:
            try:
                result = self.evaluate_topic_summary(
                    topic=topic,
                    max_articles=max_articles
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating topic '{topic}': {e}")
                results.append({
                    'topic': topic,
                    'error': str(e)
                })
        
        # Calculate aggregate statistics
        aggregate_stats = self._calculate_aggregate_stats(results)
        
        return {
            'results': results,
            'aggregate_stats': aggregate_stats,
            'total_topics': len(topics),
            'successful': sum(1 for r in results if 'evaluation' in r),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_quality_report(
        self,
        evaluation: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable quality report.
        
        Args:
            evaluation: Evaluation dictionary
        
        Returns:
            Formatted report string
        """
        metrics = evaluation['metrics']
        quality = evaluation['quality_assessment']
        
        report = []
        report.append("=" * 60)
        report.append("SUMMARY QUALITY REPORT")
        report.append("=" * 60)
        
        # Overall quality
        report.append(f"\nOverall Quality: {quality['overall'].upper()}")
        report.append(f"Score: {quality['score']:.1f}/100")
        
        # Key metrics
        report.append("\n" + "-" * 60)
        report.append("KEY METRICS")
        report.append("-" * 60)
        
        report.append(f"Compression Ratio: {metrics['compression_ratio']:.1%}")
        report.append(f"  → Summary: {metrics['summary_length']} words")
        report.append(f"  → Original: {metrics['original_length']} words")
        
        report.append(f"\nReadability (Flesch): {metrics['readability']['flesch_reading_ease']:.1f}")
        report.append(f"  → {self._interpret_flesch(metrics['readability']['flesch_reading_ease'])}")
        
        report.append(f"\nLexical Diversity: {metrics['lexical_diversity']:.1%}")
        report.append(f"Information Density: {metrics['information_density']:.1%}")
        report.append(f"Coherence: {metrics['coherence']:.1%}")
        
        # ROUGE scores if available
        if 'rouge' in metrics and metrics['rouge']:
            report.append("\n" + "-" * 60)
            report.append("ROUGE SCORES")
            report.append("-" * 60)
            for metric, scores in metrics['rouge'].items():
                report.append(f"\n{metric.upper()}:")
                report.append(f"  Precision: {scores['precision']:.3f}")
                report.append(f"  Recall: {scores['recall']:.3f}")
                report.append(f"  F-measure: {scores['fmeasure']:.3f}")
        
        # Recommendations
        report.append("\n" + "-" * 60)
        report.append("RECOMMENDATIONS")
        report.append("-" * 60)
        for rec in quality['recommendations']:
            report.append(f"• {rec}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def _assess_quality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall quality based on metrics."""
        score = 0
        max_score = 100
        recommendations = []
        
        # Compression ratio (ideal: 20-40%)
        compression = metrics['compression_ratio']
        if 0.2 <= compression <= 0.4:
            score += 20
        elif 0.1 <= compression < 0.2 or 0.4 < compression <= 0.5:
            score += 15
            recommendations.append("COMPRESSION: Consider adjusting summary length. Ideal: 20-40%")
        else:
            score += 10
            recommendations.append("COMPRESSION: Summary length may not be optimal. Ideal: 20-40%")
        
        # Readability (ideal: 60-80)
        flesch = metrics['readability']['flesch_reading_ease']
        if 60 <= flesch <= 80:
            score += 20
        elif 50 <= flesch < 60 or 80 < flesch <= 90:
            score += 15
        else:
            score += 10
            if flesch < 50:
                recommendations.append("READABILITY: Summary may be too complex. Ideal: 60-80")
            else:
                recommendations.append("READABILITY: Summary may be too simple. Ideal: 60-80")
        
        # Lexical diversity (ideal: 0.6-0.8)
        diversity = metrics['lexical_diversity']
        if 0.6 <= diversity <= 0.8:
            score += 20
        elif 0.5 <= diversity < 0.6 or 0.8 < diversity <= 0.9:
            score += 15
        else:
            score += 10
            if diversity < 0.5:
                recommendations.append("LEXICAL DIVERSITY: Consider using more varied vocabulary. Ideal: 60-80%")
        
        # Information density (ideal: 0.3-0.6)
        density = metrics['information_density']
        if 0.3 <= density <= 0.6:
            score += 20
        elif 0.2 <= density < 0.3 or 0.6 < density <= 0.7:
            score += 15
        else:
            score += 10
            if density < 0.2:
                recommendations.append("INFORMATION DENSITY: Summary may be missing key information. Ideal: 30-60%")
        
        # Coherence (ideal: > 0.3)
        coherence = metrics['coherence']
        if coherence >= 0.3:
            score += 20
        elif coherence >= 0.2:
            score += 15
        else:
            score += 10
            recommendations.append("COHERENCE: Consider improving summary coherence. Ideal: > 30%")
        
        # Determine overall quality
        if score >= 85:
            overall = "excellent"
        elif score >= 70:
            overall = "good"
        elif score >= 55:
            overall = "fair"
        else:
            overall = "needs improvement"
        
        if not recommendations:
            recommendations.append("QUALITY: Summary quality is good overall! 🎉")
        
        return {
            'score': score,
            'overall': overall,
            'recommendations': recommendations
        }
    
    def _determine_best_style(self, comparisons: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best summary style based on quality scores."""
        best_style = None
        best_score = 0
        
        for style, data in comparisons.items():
            score = data['evaluation']['quality_assessment']['score']
            if score > best_score:
                best_score = score
                best_style = style
        
        return {
            'style': best_style,
            'score': best_score
        }
    
    def _calculate_aggregate_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate statistics from batch results."""
        successful_results = [r for r in results if 'evaluation' in r]
        
        if not successful_results:
            return {}
        
        scores = [r['evaluation']['quality_assessment']['score'] for r in successful_results]
        
        return {
            'avg_quality_score': sum(scores) / len(scores),
            'min_quality_score': min(scores),
            'max_quality_score': max(scores),
            'total_evaluated': len(successful_results)
        }
    
    def _interpret_flesch(self, score: float) -> str:
        """Interpret Flesch Reading Ease score."""
        if score >= 90:
            return "Very easy to read"
        elif score >= 80:
            return "Easy to read"
        elif score >= 70:
            return "Fairly easy to read"
        elif score >= 60:
            return "Standard/Average"
        elif score >= 50:
            return "Fairly difficult to read"
        elif score >= 30:
            return "Difficult to read"
        else:
            return "Very difficult to read"


# Example usage and testing
if __name__ == "__main__":
    import sys
    from config import get_settings
    
    print("=" * 60)
    print("Validation Pipeline - Testing")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.openai_api_key:
        print("\n⚠️  OPENAI_API_KEY not set. Skipping full pipeline test.")
        print("Testing metrics only...\n")
        
        # Test metrics only
        metrics = SummaryMetrics()
        
        original = "AI is transforming technology through machine learning and deep learning."
        summary = "AI transforms technology via ML and DL."
        
        result = metrics.calculate_all_metrics(summary, original)
        print(f"Compression: {result['compression_ratio']:.1%}")
        print(f"Readability: {result['readability']['flesch_reading_ease']:.1f}")
        print("\n✅ Metrics test completed!")
        sys.exit(0)
    
    try:
        # Initialize pipeline
        print("\n[1/2] Initializing validation pipeline...")
        pipeline = ValidationPipeline()
        print("   ✅ Pipeline initialized")
        
        # Test evaluation
        print("\n[2/2] Testing summary evaluation...")
        result = pipeline.evaluate_topic_summary(
            topic="technology",
            max_articles=2,
            summary_length=100
        )
        
        if 'evaluation' in result:
            print(f"   Topic: {result['topic']}")
            print(f"   Quality: {result['evaluation']['quality_assessment']['overall']}")
            print(f"   Score: {result['evaluation']['quality_assessment']['score']:.1f}/100")
            
            # Generate report
            report = pipeline.generate_quality_report(result['evaluation'])
            print("\n" + report)
        
        print("\n✅ Validation pipeline test completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
