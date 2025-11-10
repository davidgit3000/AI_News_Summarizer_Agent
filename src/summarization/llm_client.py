"""
LLM client for text summarization using OpenAI API.
Handles API calls, prompt formatting, and response processing.
"""

import logging
from typing import List, Dict, Optional, Any
from openai import OpenAI
from openai import OpenAIError

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenAI LLM API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (uses config if None)
            model: Model name (uses config if None)
            temperature: Temperature for generation (uses config if None)
            max_tokens: Max tokens for response (uses config if None)
        """
        settings = get_settings()
        
        # Set up API key
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY in .env")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Set parameters
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        
        logger.info(f"LLMClient initialized with model: {self.model}")
    
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: User prompt
            system_message: System message for context
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Enable streaming (not implemented yet)
            model: Override default model (e.g., "gpt-4")
        
        Returns:
            Generated text
        """
        try:
            # Build messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Set parameters
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens or self.max_tokens
            model_to_use = model or self.model
            
            # Make API call
            logger.debug(f"Calling OpenAI API with model: {model_to_use}")
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )
            
            # Extract response
            generated_text = response.choices[0].message.content
            
            # Log usage
            if hasattr(response, 'usage'):
                logger.debug(f"Tokens used: {response.usage.total_tokens}")
            
            return generated_text
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    def summarize(
        self,
        text: str,
        max_length: int = 150,
        style: str = "concise"
    ) -> str:
        """
        Summarize a single text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length in words
            style: Summary style (concise, detailed, bullet_points)
        
        Returns:
            Summary text
        """
        # Truncate text if too long to avoid context window issues
        # GPT-3.5-turbo has 4K tokens (~3000 words), leave room for prompt and response
        max_input_words = 2500
        words = text.split()
        if len(words) > max_input_words:
            logger.warning(f"Text too long ({len(words)} words), truncating to {max_input_words} words")
            text = ' '.join(words[:max_input_words]) + "\n\n[Article truncated due to length]"
        
        # Build prompt based on style
        if style == "bullet_points":
            prompt = f"""Summarize the following text in bullet points (max {max_length} words):

{text}

IMPORTANT: If the article content is inaccessible or requires a subscription (NOT just truncated), clearly state "Article content unavailable" or "Subscription required" instead of fabricating information. If the article is truncated but has substantial content, summarize what's available.

Summary (bullet points):"""
            system_message = "You are a professional news analyst. Summarize information in clear bullet points. Never fabricate information - if content is unavailable, say so."
        
        elif style == "comprehensive" or style == "detailed":
            prompt = f"""Provide a detailed, comprehensive summary of the following text (max {max_length} words):

{text}

IMPORTANT: If the article content is inaccessible or requires a subscription (NOT just truncated), clearly state "Article content unavailable" or "Subscription required" instead of fabricating information. If the article is truncated but has substantial content, summarize what's available.

Comprehensive summary:"""
            system_message = "You are a professional news analyst. Provide comprehensive, well-structured summaries. Never fabricate information - if content is unavailable, say so."
        
        elif style == "executive":
            prompt = f"""Provide an executive summary of the following text (max {max_length} words).
Focus on business impact, key decisions, strategic implications, and actionable insights:

{text}

IMPORTANT: If the article content is inaccessible or requires a subscription (NOT just truncated), clearly state "Article content unavailable" or "Subscription required" instead of fabricating information. If the article is truncated but has substantial content, summarize what's available.

Executive summary:"""
            system_message = "You are a business analyst. Provide executive summaries focused on strategic impact and business value. Never fabricate information - if content is unavailable, say so."
        
        elif style == "technical":
            prompt = f"""Provide a technical summary of the following text (max {max_length} words).
Include technical details, methodologies, specifications, and key technical insights:

{text}

IMPORTANT: If the article content is inaccessible or requires a subscription (NOT just truncated), clearly state "Article content unavailable" or "Subscription required" instead of fabricating information. If the article is truncated but has substantial content, summarize what's available.

Technical summary:"""
            system_message = "You are a technical analyst. Provide detailed technical summaries with specific methodologies and technical details. Never fabricate information - if content is unavailable, say so."
        
        elif style == "eli5":
            prompt = f"""Explain the following text in very simple terms (max {max_length} words).
Use short sentences (under 15 words each), simple everyday words, and avoid technical jargon.
Write as if explaining to a 10-year-old:

{text}

IMPORTANT: If the article content is inaccessible, incomplete, or requires a subscription, simply say "The article cannot be accessed" instead of making up information.

Simple explanation:"""
            system_message = "You are an expert at explaining complex topics simply. Use short sentences, simple words, and everyday language. Avoid jargon and technical terms. Never make up information - if content is unavailable, say so."
        
        else:  # concise (default)
            prompt = f"""Provide a concise summary of the following text (max {max_length} words):

{text}

IMPORTANT: If the article content is inaccessible or requires a subscription (NOT just truncated), clearly state "Article content unavailable" or "Subscription required" instead of fabricating information. If the article is truncated but has substantial content, summarize what's available.

Summary:"""
            system_message = "You are a professional news summarizer. Provide accurate, concise summaries. Never fabricate information - if content is unavailable, say so."
        
        return self.generate(
            prompt=prompt,
            system_message=system_message,
            max_tokens=max_length * 2  # Rough token estimate
        )
    
    def summarize_multiple(
        self,
        texts: List[str],
        max_length: int = 200,
        combine: bool = True
    ) -> str:
        """
        Summarize multiple texts.
        
        Args:
            texts: List of texts to summarize
            max_length: Maximum length in words
            combine: If True, create one combined summary
        
        Returns:
            Combined summary or list of summaries
        """
        if combine:
            # Combine texts and summarize together
            combined_text = "\n\n---\n\n".join(texts)
            
            prompt = f"""Summarize the following articles into one cohesive summary (max {max_length} words):

{combined_text}

IMPORTANT: If any article content is inaccessible, incomplete, or requires a subscription, note which articles are unavailable instead of fabricating information.

Combined summary:"""
            
            system_message = "You are a professional news summarizer. Synthesize multiple articles into one clear summary. Never fabricate information - if content is unavailable, acknowledge it."
            
            return self.generate(
                prompt=prompt,
                system_message=system_message,
                max_tokens=max_length * 2
            )
        else:
            # Summarize each text separately
            summaries = []
            for text in texts:
                summary = self.summarize(text, max_length=max_length // len(texts))
                summaries.append(summary)
            return "\n\n".join(summaries)
    
    def extract_key_points(
        self,
        text: str,
        num_points: int = 5
    ) -> List[str]:
        """
        Extract key points from text.
        
        Args:
            text: Text to analyze
            num_points: Number of key points to extract
        
        Returns:
            List of key points
        """
        prompt = f"""Extract the {num_points} most important key points from the following text.
Return only the key points, one per line, without numbering.

{text}

Key points:"""
        
        system_message = "You are an expert at identifying key information in news articles."
        
        response = self.generate(
            prompt=prompt,
            system_message=system_message,
            max_tokens=200
        )
        
        # Parse response into list
        points = [line.strip() for line in response.strip().split('\n') if line.strip()]
        return points[:num_points]
    
    def answer_question(
        self,
        context: str,
        question: str,
        use_web_search: bool = False
    ) -> str:
        """
        Answer a question based on provided context, optionally using web search.
        
        Args:
            context: Context text from articles
            question: Question to answer
            use_web_search: If True, use web search to enhance answers
        
        Returns:
            Answer text
        """
        if use_web_search:
            # Use GPT-4 for better answers with more recent knowledge
            prompt = f"""Answer the following question using both the article context and your general knowledge.

Article Context:
{context}

Question: {question}

IMPORTANT: 
1. First check the article context for relevant information.
2. If the article context is insufficient, use web search to provide accurate, up-to-date definitions and background information.
3. Return either from article context or web search results.
4. For recent topics (2023-2024), rely more on article context as it may be more current.
5. Always prioritize factual accuracy.

Answer:"""
            
            system_message = "You are a helpful assistant with extensive knowledge. Provide accurate, comprehensive answers by combining article context with your general knowledge. Always prioritize factual accuracy."
            
            # Use GPT-4o for web search mode
            return self.generate(
                prompt=prompt,
                system_message=system_message,
                max_tokens=300,
                temperature=0.3,
                model="gpt-4.1"
            )
        else:
            # Original context-only approach
            prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {question}

IMPORTANT: Answer based on the information available in the context. If the context contains relevant information, provide a clear answer even if the context is partial or truncated. Only say "Cannot answer - insufficient information in the provided context" if the context is completely empty or contains no relevant information at all.

Answer:"""
            
            system_message = "You are a helpful assistant that answers questions based on provided context. Use the available information to provide helpful answers. Only refuse to answer if the context is completely empty or contains no relevant information."
        
        return self.generate(
            prompt=prompt,
            system_message=system_message,
            max_tokens=300
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model info
        """
        return {
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }


# Example usage and testing
if __name__ == "__main__":
    import os
    
    print("=" * 60)
    print("LLM Client - Testing")
    print("=" * 60)
    
    # Check API key
    settings = get_settings()
    if not settings.openai_api_key:
        print("\n❌ Error: OPENAI_API_KEY not set in .env file")
        print("Please add your OpenAI API key to continue.")
        exit(1)
    
    try:
        # Initialize client
        print("\n[1/4] Initializing LLM client...")
        client = LLMClient()
        info = client.get_model_info()
        print(f"   Model: {info['model']}")
        print(f"   Temperature: {info['temperature']}")
        print(f"   Max tokens: {info['max_tokens']}")
        print("   ✅ Client initialized")
        
        # Test basic generation
        print("\n[2/4] Testing basic text generation...")
        prompt = "What is artificial intelligence in one sentence?"
        response = client.generate(prompt)
        print(f"   Prompt: {prompt}")
        print(f"   Response: {response}")
        print("   ✅ Generation working")
        
        # Test summarization
        print("\n[3/4] Testing summarization...")
        sample_text = """
        Artificial intelligence (AI) is transforming the technology industry at an unprecedented pace.
        Machine learning models are becoming more sophisticated, enabling computers to perform tasks
        that previously required human intelligence. Deep learning, a subset of machine learning,
        uses neural networks with multiple layers to process complex patterns in data. Companies
        are investing billions in AI research and development, leading to breakthroughs in natural
        language processing, computer vision, and autonomous systems. However, concerns about AI
        safety, ethics, and job displacement remain important topics of discussion.
        """
        
        summary = client.summarize(sample_text, max_length=50, style="concise")
        print(f"   Original length: {len(sample_text.split())} words")
        print(f"   Summary: {summary}")
        print(f"   Summary length: {len(summary.split())} words")
        print("   ✅ Summarization working")
        
        # Test key point extraction
        print("\n[4/4] Testing key point extraction...")
        key_points = client.extract_key_points(sample_text, num_points=3)
        print(f"   Extracted {len(key_points)} key points:")
        for i, point in enumerate(key_points, 1):
            print(f"   {i}. {point}")
        print("   ✅ Key point extraction working")
        
        print("\n" + "=" * 60)
        print("✅ LLM client test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
