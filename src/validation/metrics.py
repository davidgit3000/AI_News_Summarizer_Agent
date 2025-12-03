"""
Validation metrics for evaluating summary quality.
Includes ROUGE scores, readability, and other quality metrics.
"""

import logging
from typing import Dict, List, Optional, Any
import re
from collections import Counter
import math

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    logging.warning("rouge-score not installed. ROUGE metrics will not be available.")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("nltk not installed. Some metrics will not be available.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SummaryMetrics:
    """Calculate various metrics for summary quality evaluation."""
    
    def __init__(self):
        """Initialize the metrics calculator."""
        # Initialize ROUGE scorer if available
        if ROUGE_AVAILABLE:
            self.rouge_scorer = rouge_scorer.RougeScorer(
                ['rouge1', 'rouge2', 'rougeL'],
                use_stemmer=True
            )
        else:
            self.rouge_scorer = None
        
        # Download NLTK data if needed
        if NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                logger.info("Downloading NLTK punkt tokenizer...")
                nltk.download('punkt', quiet=True)
    
    def calculate_rouge_scores(
        self,
        summary: str,
        reference: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate ROUGE scores comparing summary to reference.
        
        Args:
            summary: Generated summary
            reference: Reference text (original article or human summary)
        
        Returns:
            Dictionary with ROUGE-1, ROUGE-2, ROUGE-L scores
        """
        if not ROUGE_AVAILABLE:
            logger.warning("ROUGE scorer not available")
            return {}
        
        if not summary or not reference:
            logger.warning("Empty summary or reference")
            return {}
        
        try:
            scores = self.rouge_scorer.score(reference, summary)
            
            # Format scores
            result = {}
            for metric, score in scores.items():
                result[metric] = {
                    'precision': score.precision,
                    'recall': score.recall,
                    'fmeasure': score.fmeasure
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating ROUGE scores: {e}")
            return {}
    
    def calculate_compression_ratio(
        self,
        summary: str,
        original: str
    ) -> float:
        """
        Calculate compression ratio (summary length / original length).
        
        Args:
            summary: Summary text
            original: Original text
        
        Returns:
            Compression ratio (0-1)
        """
        summary_words = len(summary.split())
        original_words = len(original.split())
        
        if original_words == 0:
            return 0.0
        
        return summary_words / original_words
    
    def calculate_readability_score(self, text: str) -> Dict[str, float]:
        """
        Calculate readability metrics (Flesch Reading Ease, etc.).
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with readability scores
        """
        if not text:
            return {'flesch_reading_ease': 0.0, 'avg_sentence_length': 0.0}
        
        # Count sentences and words
        sentences = self._split_sentences(text)
        words = text.split()
        
        num_sentences = len(sentences)
        num_words = len(words)
        
        if num_sentences == 0 or num_words == 0:
            return {'flesch_reading_ease': 0.0, 'avg_sentence_length': 0.0}
        
        # Count syllables (approximation)
        num_syllables = sum(self._count_syllables(word) for word in words)
        
        # Flesch Reading Ease
        # Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        avg_sentence_length = num_words / num_sentences
        avg_syllables_per_word = num_syllables / num_words
        
        flesch = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        return {
            'flesch_reading_ease': max(0, min(100, flesch)),  # Clamp to 0-100
            'avg_sentence_length': avg_sentence_length,
            'avg_syllables_per_word': avg_syllables_per_word
        }
    
    def calculate_lexical_diversity(self, text: str) -> float:
        """
        Calculate lexical diversity (unique words / total words).
        
        Args:
            text: Text to analyze
        
        Returns:
            Lexical diversity score (0-1)
        """
        words = text.lower().split()
        
        if not words:
            return 0.0
        
        unique_words = len(set(words))
        total_words = len(words)
        
        return unique_words / total_words
    
    def calculate_information_density(
        self,
        summary: str,
        original: str
    ) -> float:
        """
        Calculate information density (key terms preserved).
        
        Args:
            summary: Summary text
            original: Original text
        
        Returns:
            Information density score (0-1)
        """
        # Extract key terms (simple approach: words longer than 5 chars)
        summary_terms = set(
            word.lower() for word in summary.split()
            if len(word) > 5 and word.isalpha()
        )
        original_terms = set(
            word.lower() for word in original.split()
            if len(word) > 5 and word.isalpha()
        )
        
        if not original_terms:
            return 0.0
        
        # Calculate overlap
        overlap = len(summary_terms & original_terms)
        return overlap / len(original_terms)
    
    def calculate_coherence_score(self, text: str) -> float:
        """
        Calculate coherence score using both word overlap and discourse connectives.
        
        Args:
            text: Text to analyze
        
        Returns:
            Coherence score (0-1)
        """
        sentences = self._split_sentences(text)
        num_sentences = len(sentences)
        
        if num_sentences <= 1:
            return 1.0  # Single sentence is perfectly coherent
        
        # Part 1: Calculate word overlap between consecutive sentences
        overlap_scores = []
        for i in range(len(sentences) - 1):
            sent1_words = set(sentences[i].lower().split())
            sent2_words = set(sentences[i + 1].lower().split())
            
            # Remove common stop words for better signal
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
            sent1_words = sent1_words - stop_words
            sent2_words = sent2_words - stop_words
            
            if not sent1_words or not sent2_words:
                continue
            
            # Calculate Jaccard similarity
            intersection = len(sent1_words & sent2_words)
            union = len(sent1_words | sent2_words)
            
            if union > 0:
                overlap_scores.append(intersection / union)
        
        # Average overlap score
        overlap_score = sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
        
        # Part 2: Check for discourse connectives
        connectives = [
            'however', 'therefore', 'moreover', 'furthermore', 'additionally',
            'consequently', 'meanwhile', 'nevertheless', 'thus', 'hence',
            'also', 'besides', 'indeed', 'in addition', 'for example',
            'similarly', 'likewise', 'in contrast', 'on the other hand',
            'as a result', 'in fact', 'specifically', 'particularly'
        ]
        
        text_lower = text.lower()
        connective_count = sum(1 for conn in connectives if conn in text_lower)
        
        # Normalize connective score (1 connective per 2 sentences is good)
        connective_score = min(1.0, connective_count / max(1, (num_sentences / 2)))
        
        # Combine both scores (70% overlap, 30% connectives)
        final_score = (0.7 * overlap_score) + (0.3 * connective_score)
        
        return final_score
    
    def calculate_all_metrics(
        self,
        summary: str,
        original: str,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate all available metrics.
        
        Args:
            summary: Generated summary
            original: Original text
            reference: Reference summary (optional, for ROUGE)
        
        Returns:
            Dictionary with all metrics
        """
        metrics = {}
        
        # ROUGE scores (if reference provided)
        if reference and ROUGE_AVAILABLE:
            metrics['rouge'] = self.calculate_rouge_scores(summary, reference)
        
        # Compression ratio
        metrics['compression_ratio'] = self.calculate_compression_ratio(summary, original)
        
        # Readability
        metrics['readability'] = self.calculate_readability_score(summary)
        
        # Lexical diversity
        metrics['lexical_diversity'] = self.calculate_lexical_diversity(summary)
        
        # Information density
        metrics['information_density'] = self.calculate_information_density(summary, original)
        
        # Coherence
        metrics['coherence'] = self.calculate_coherence_score(summary)
        
        # Length metrics
        metrics['summary_length'] = len(summary.split())
        metrics['original_length'] = len(original.split())
        
        return metrics
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if NLTK_AVAILABLE:
            try:
                return sent_tokenize(text)
            except:
                pass
        
        # Fallback: simple split on punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word (approximation).
        
        Args:
            word: Word to count syllables
        
        Returns:
            Estimated syllable count
        """
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e'):
            syllable_count -= 1
        
        # Ensure at least 1 syllable
        return max(1, syllable_count)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("Summary Metrics - Testing")
    print("=" * 60)
    
    # Initialize metrics
    print("\n[1/5] Initializing metrics calculator...")
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
    
    # Test compression ratio
    print("\n[2/5] Testing compression ratio...")
    ratio = metrics.calculate_compression_ratio(summary, original)
    print(f"   Original: {len(original.split())} words")
    print(f"   Summary: {len(summary.split())} words")
    print(f"   Compression ratio: {ratio:.2%}")
    print("   ✅ Compression ratio calculated")
    
    # Test readability
    print("\n[3/5] Testing readability...")
    readability = metrics.calculate_readability_score(summary)
    print(f"   Flesch Reading Ease: {readability['flesch_reading_ease']:.1f}")
    print(f"   Avg sentence length: {readability['avg_sentence_length']:.1f} words")
    print("   ✅ Readability calculated")
    
    # Test lexical diversity
    print("\n[4/5] Testing lexical diversity...")
    diversity = metrics.calculate_lexical_diversity(summary)
    print(f"   Lexical diversity: {diversity:.2%}")
    print("   ✅ Lexical diversity calculated")
    
    # Test all metrics
    print("\n[5/5] Testing all metrics...")
    all_metrics = metrics.calculate_all_metrics(summary, original)
    print(f"   Compression: {all_metrics['compression_ratio']:.2%}")
    print(f"   Information density: {all_metrics['information_density']:.2%}")
    print(f"   Coherence: {all_metrics['coherence']:.2%}")
    print("   ✅ All metrics calculated")
    
    print("\n" + "=" * 60)
    print("✅ Metrics test completed!")
    print("=" * 60)
