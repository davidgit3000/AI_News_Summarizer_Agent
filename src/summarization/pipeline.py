"""
RAG-based summarization pipeline.
Integrates retrieval and LLM for context-aware news summarization.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.summarization.llm_client import LLMClient
from src.retrieval.pipeline import RetrievalPipeline
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SummarizationPipeline:
    """Pipeline for RAG-based news summarization."""
    
    def __init__(
        self,
        llm_model: Optional[str] = None,
        retrieval_pipeline: Optional[RetrievalPipeline] = None
    ):
        """
        Initialize the summarization pipeline.
        
        Args:
            llm_model: LLM model name (optional)
            retrieval_pipeline: Existing retrieval pipeline (optional)
        """
        self.settings = get_settings()
        self.llm_client = LLMClient(model=llm_model)
        self.retrieval_pipeline = retrieval_pipeline or RetrievalPipeline()
        
        logger.info("SummarizationPipeline initialized successfully")
    
    def summarize_topic(
        self,
        topic: str,
        max_articles: int = 5,
        summary_length: int = 200,
        style: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Summarize news articles about a topic using RAG.
        
        Args:
            topic: Topic to summarize
            max_articles: Maximum number of articles to retrieve
            summary_length: Target summary length in words
            style: Summary style (comprehensive, concise, bullet_points)
        
        Returns:
            Dictionary with summary and metadata
        """
        logger.info(f"Summarizing topic: '{topic}'")
        
        # Step 1: Retrieve relevant articles
        context_data = self.retrieval_pipeline.retrieve_context_for_summarization(
            topic=topic,
            max_articles=max_articles
        )
        
        if not context_data['context']:
            logger.warning(f"No articles found for topic: {topic}")
            return {
                'topic': topic,
                'summary': "No relevant articles found for this topic.",
                'sources': [],
                'article_count': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        # Step 2: Build prompt based on style
        prompt = self._build_summarization_prompt(
            topic=topic,
            context=context_data['context'],
            style=style,
            max_length=summary_length
        )
        
        # Step 3: Generate summary
        logger.debug("Generating summary with LLM...")
        summary = self.llm_client.generate(
            prompt=prompt,
            system_message=self._get_system_message(style),
            max_tokens=summary_length * 2
        )
        
        # Step 4: Format result
        result = {
            'topic': topic,
            'summary': summary.strip(),
            'sources': context_data['sources'],
            'articles': context_data['articles'],  # Include full articles for validation
            'article_count': context_data['article_count'],
            'style': style,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Summary generated: {len(summary.split())} words from {result['article_count']} articles")
        return result
    
    def summarize_with_questions(
        self,
        topic: str,
        questions: List[str],
        max_articles: int = 5
    ) -> Dict[str, Any]:
        """
        Summarize a topic and answer specific questions.
        
        Args:
            topic: Topic to summarize
            questions: List of questions to answer
            max_articles: Maximum articles to retrieve
        
        Returns:
            Dictionary with summary and answers
        """
        logger.info(f"Summarizing topic with {len(questions)} questions")
        
        # Retrieve context
        context_data = self.retrieval_pipeline.retrieve_context_for_summarization(
            topic=topic,
            max_articles=max_articles
        )
        
        if not context_data['context']:
            return {
                'topic': topic,
                'summary': "No relevant articles found.",
                'answers': {},
                'sources': []
            }
        
        # Generate summary
        summary_prompt = f"""Based on the following articles about {topic}, provide a comprehensive summary.

{context_data['context']}

Summary:"""
        
        summary = self.llm_client.generate(
            prompt=summary_prompt,
            system_message="You are a professional news analyst.",
            max_tokens=300
        )
        
        # Answer questions
        answers = {}
        for question in questions:
            answer = self.llm_client.answer_question(
                context=context_data['context'],
                question=question
            )
            answers[question] = answer.strip()
        
        return {
            'topic': topic,
            'summary': summary.strip(),
            'answers': answers,
            'sources': context_data['sources'],
            'article_count': context_data['article_count'],
            'timestamp': datetime.now().isoformat()
        }
    
    def compare_sources(
        self,
        topic: str,
        sources: List[str],
        max_articles_per_source: int = 3
    ) -> Dict[str, Any]:
        """
        Compare how different sources cover a topic.
        
        Args:
            topic: Topic to compare
            sources: List of source names
            max_articles_per_source: Articles per source
        
        Returns:
            Dictionary with comparison analysis
        """
        logger.info(f"Comparing {len(sources)} sources on topic: {topic}")
        
        source_summaries = {}
        all_sources_info = []
        
        # Get articles from each source
        for source in sources:
            articles = self.retrieval_pipeline.search_by_source(
                query=topic,
                source=source,
                top_k=max_articles_per_source
            )
            
            if articles:
                # Summarize this source's coverage
                context = "\n\n".join([a['document'] for a in articles])
                
                prompt = f"""Summarize how {source} covers {topic} based on these articles:

{context}

Summary of {source}'s coverage:"""
                
                summary = self.llm_client.generate(
                    prompt=prompt,
                    max_tokens=150
                )
                
                source_summaries[source] = summary.strip()
                all_sources_info.extend([
                    {
                        'source': source,
                        'title': a['metadata'].get('title', ''),
                        'similarity': a['similarity']
                    }
                    for a in articles
                ])
        
        # Generate comparison
        if len(source_summaries) > 1:
            comparison_text = "\n\n".join([
                f"{source}: {summary}"
                for source, summary in source_summaries.items()
            ])
            
            comparison_prompt = f"""Compare how different news sources cover {topic}:

{comparison_text}

Comparison analysis:"""
            
            comparison = self.llm_client.generate(
                prompt=comparison_prompt,
                system_message="You are a media analyst comparing news coverage.",
                max_tokens=200
            )
        else:
            comparison = "Not enough sources to compare."
        
        return {
            'topic': topic,
            'sources_compared': list(source_summaries.keys()),
            'source_summaries': source_summaries,
            'comparison': comparison.strip(),
            'articles': all_sources_info,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_headline(
        self,
        topic: str,
        max_articles: int = 3
    ) -> str:
        """
        Generate a headline for a topic based on articles.
        
        Args:
            topic: Topic to generate headline for
            max_articles: Number of articles to consider
        
        Returns:
            Generated headline
        """
        context_data = self.retrieval_pipeline.retrieve_context_for_summarization(
            topic=topic,
            max_articles=max_articles
        )
        
        if not context_data['context']:
            return f"No recent news about {topic}"
        
        prompt = f"""Based on these articles about {topic}, generate a compelling news headline (max 15 words):

{context_data['context'][:1000]}

Headline:"""
        
        headline = self.llm_client.generate(
            prompt=prompt,
            system_message="You are a professional headline writer.",
            max_tokens=30
        )
        
        return headline.strip().strip('"')
    
    def extract_key_insights(
        self,
        topic: str,
        num_insights: int = 5,
        max_articles: int = 5
    ) -> Dict[str, Any]:
        """
        Extract key insights from articles about a topic.
        
        Args:
            topic: Topic to analyze
            num_insights: Number of insights to extract
            max_articles: Maximum articles to analyze
        
        Returns:
            Dictionary with insights and sources
        """
        logger.info(f"Extracting {num_insights} key insights for: {topic}")
        
        context_data = self.retrieval_pipeline.retrieve_context_for_summarization(
            topic=topic,
            max_articles=max_articles
        )
        
        if not context_data['context']:
            return {
                'topic': topic,
                'insights': [],
                'sources': []
            }
        
        # Extract insights
        insights = self.llm_client.extract_key_points(
            text=context_data['context'],
            num_points=num_insights
        )
        
        return {
            'topic': topic,
            'insights': insights,
            'sources': context_data['sources'],
            'article_count': context_data['article_count'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _build_summarization_prompt(
        self,
        topic: str,
        context: str,
        style: str,
        max_length: int
    ) -> str:
        """Build prompt for summarization based on style."""
        
        if style == "bullet_points":
            return f"""Based on the following articles about {topic}, create a summary in bullet points (max {max_length} words).

Articles:
{context}

Summary (bullet points):"""
        
        elif style == "concise":
            return f"""Based on the following articles about {topic}, provide a concise summary (max {max_length} words). 
Synthesize the information into a cohesive narrative, not a list of articles.

Articles:
{context}

Concise summary:"""
        
        elif style == "executive":
            return f"""Based on the following articles about {topic}, provide an executive summary (max {max_length} words).
Focus on business impact, key decisions, strategic implications, and actionable insights.
Synthesize the information into a cohesive narrative.

Articles:
{context}

Executive summary:"""
        
        elif style == "technical":
            return f"""Based on the following articles about {topic}, provide a technical summary (max {max_length} words).
Include technical details, methodologies, specifications, and key technical insights.
Synthesize the information into a cohesive narrative.

Articles:
{context}

Technical summary:"""
        
        elif style == "eli5":
            return f"""Based on the following articles about {topic}, explain the topic in very simple terms (max {max_length} words).
Use short sentences (under 15 words each), simple everyday words, and avoid technical jargon.
Write as if explaining to a 10-year-old.

Articles:
{context}

Simple explanation:"""
        
        else:  # comprehensive
            return f"""Based on the following articles about {topic}, provide a comprehensive summary that covers the main points and key developments (max {max_length} words).
Synthesize the information into a cohesive narrative, not a list of articles.

Articles:
{context}

Comprehensive summary:"""
    
    def _get_system_message(self, style: str) -> str:
        """Get system message based on style."""
        
        if style == "bullet_points":
            return "You are a professional news analyst. Summarize information in clear bullet points."
        elif style == "concise":
            return "You are a professional news summarizer. Provide concise, accurate summaries."
        elif style == "executive":
            return "You are a business analyst. Provide executive summaries focused on strategic impact and business value."
        elif style == "technical":
            return "You are a technical analyst. Provide detailed technical summaries with specific methodologies and technical details."
        elif style == "eli5":
            return "You are an expert at explaining complex topics simply. Use short sentences, simple words, and everyday language. Avoid jargon and technical terms."
        else:  # comprehensive
            return "You are a professional news analyst. Provide comprehensive, well-structured summaries."


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Summarization Pipeline - Testing")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.openai_api_key:
        print("\n❌ Error: OPENAI_API_KEY not set in .env file")
        print("Please add your OpenAI API key to continue.")
        sys.exit(1)
    
    try:
        # Initialize pipeline
        print("\n[1/3] Initializing summarization pipeline...")
        pipeline = SummarizationPipeline()
        print("   ✅ Pipeline initialized")
        
        # Test topic summarization
        print("\n[2/3] Testing topic summarization...")
        topic = "artificial intelligence"
        result = pipeline.summarize_topic(
            topic=topic,
            max_articles=2,
            summary_length=100,
            style="concise"
        )
        
        print(f"   Topic: {result['topic']}")
        print(f"   Articles used: {result['article_count']}")
        print(f"   Summary length: {len(result['summary'].split())} words")
        print(f"\n   Summary:\n   {result['summary']}")
        print("\n   ✅ Topic summarization working")
        
        # Test headline generation
        print("\n[3/3] Testing headline generation...")
        headline = pipeline.generate_headline(topic, max_articles=2)
        print(f"   Generated headline: {headline}")
        print("   ✅ Headline generation working")
        
        print("\n" + "=" * 60)
        print("✅ Summarization pipeline test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
