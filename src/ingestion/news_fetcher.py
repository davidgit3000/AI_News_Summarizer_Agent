"""
News fetcher module for retrieving articles from NewsAPI.
Handles API requests, pagination, and error handling.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import requests

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches news articles from NewsAPI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the news fetcher.
        
        Args:
            api_key: NewsAPI key. If None, loads from settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.newsapi_key
        
        if not self.api_key:
            raise ValueError(
                "NewsAPI key not found. Please set NEWSAPI_KEY in your .env file"
            )
        
        self.base_url = "https://newsapi.org/v2"
        self.language = settings.news_api_language
        self.page_size = settings.news_api_page_size
        self.sources = settings.news_api_sources
        
        logger.info("NewsFetcher initialized successfully")
    
    def fetch_top_headlines(
        self,
        query: Optional[str] = None,
        sources: Optional[str] = None,
        category: Optional[str] = None,
        country: Optional[str] = None,
        page_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch top headlines from NewsAPI.
        
        Args:
            query: Keywords or phrases to search for
            sources: Comma-separated news sources (e.g., 'bbc-news,cnn')
            category: Category (business, entertainment, general, health, science, sports, technology)
            country: 2-letter ISO country code (e.g., 'us', 'gb')
            page_size: Number of results to return (max 100)
        
        Returns:
            List of article dictionaries
        """
        try:
            # Use sources from parameter, or fall back to config if not provided
            # But only if config has actual sources (not empty string)
            sources_to_use = sources if sources else (self.sources if self.sources else None)
            
            params = {
                'q': query,
                'sources': sources_to_use,
                'category': category,
                'country': country,
                'language': self.language,
                'page_size': page_size or self.page_size
            }
            
            # Remove None and empty string values
            params = {k: v for k, v in params.items() if v is not None and v != ''}
            
            # Note: sources parameter cannot be mixed with country/category
            if 'sources' in params and ('country' in params or 'category' in params):
                params.pop('country', None)
                params.pop('category', None)
            
            logger.info(f"Fetching top headlines with params: {params}")
            
            # Make API request
            headers = {'X-Api-Key': self.api_key}
            response = requests.get(
                f"{self.base_url}/top-headlines",
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            articles = data.get('articles', [])
            logger.info(f"Successfully fetched {len(articles)} articles")
            
            return self._process_articles(articles)
            
        except requests.RequestException as e:
            logger.error(f"NewsAPI request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching headlines: {e}")
            raise
    
    def fetch_everything(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sources: Optional[str] = None,
        domains: Optional[str] = None,
        sort_by: str = 'publishedAt',
        page_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search through millions of articles from NewsAPI.
        
        Args:
            query: Keywords or phrases to search for (required)
            from_date: Oldest article date
            to_date: Newest article date
            sources: Comma-separated news sources
            domains: Comma-separated domains (e.g., 'bbc.co.uk,techcrunch.com')
            sort_by: Sort order ('relevancy', 'popularity', 'publishedAt')
            page_size: Number of results (max 100)
        
        Returns:
            List of article dictionaries
        """
        try:
            # Default to last 7 days if no dates specified
            if not from_date:
                from_date = datetime.now() - timedelta(days=7)
            if not to_date:
                to_date = datetime.now()
            
            params = {
                'q': query,
                'from_param': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'sources': sources or self.sources,
                'domains': domains,
                'language': self.language,
                'sort_by': sort_by,
                'page_size': page_size or self.page_size
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            logger.info(f"Searching articles with params: {params}")
            
            # Make API request
            headers = {'X-Api-Key': self.api_key}
            response = requests.get(
                f"{self.base_url}/everything",
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            articles = data.get('articles', [])
            logger.info(f"Successfully fetched {len(articles)} articles")
            
            return self._process_articles(articles)
            
        except requests.RequestException as e:
            logger.error(f"NewsAPI request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error searching articles: {e}")
            raise
    
    def fetch_by_topic(
        self,
        topic: str,
        days_back: int = 7,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Convenience method to fetch articles about a specific topic.
        
        Args:
            topic: Topic to search for
            days_back: How many days back to search
            max_results: Maximum number of results
        
        Returns:
            List of article dictionaries
        """
        from_date = datetime.now() - timedelta(days=days_back)
        
        return self.fetch_everything(
            query=topic,
            from_date=from_date,
            sort_by='relevancy',
            page_size=max_results
        )
    
    def _process_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """
        Process and clean article data.
        
        Args:
            articles: Raw articles from NewsAPI
        
        Returns:
            Processed article dictionaries
        """
        processed = []
        
        for article in articles:
            # Skip articles without content
            if not article.get('content') and not article.get('description'):
                continue
            
            processed_article = {
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'author': article.get('author', 'Unknown'),
                'published_at': article.get('publishedAt', ''),
                'url_to_image': article.get('urlToImage', ''),
                'fetched_at': datetime.now().isoformat()
            }
            
            processed.append(processed_article)
        
        return processed
    
    def get_sources(self, category: Optional[str] = None, language: Optional[str] = None) -> List[Dict]:
        """
        Get available news sources.
        
        Args:
            category: Filter by category
            language: Filter by language
        
        Returns:
            List of source dictionaries
        """
        try:
            params = {
                'category': category,
                'language': language or self.language
            }
            params = {k: v for k, v in params.items() if v is not None}
            
            # Make API request
            headers = {'X-Api-Key': self.api_key}
            response = requests.get(
                f"{self.base_url}/sources",
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            sources = data.get('sources', [])
            logger.info(f"Found {len(sources)} sources")
            return sources
            
        except requests.RequestException as e:
            logger.error(f"Error fetching sources: {e}")
            raise


# Example usage
if __name__ == "__main__":
    try:
        # Initialize fetcher
        fetcher = NewsFetcher()
        
        # Fetch top headlines
        print("\n=== Fetching Top Headlines ===")
        headlines = fetcher.fetch_top_headlines(page_size=5)
        for i, article in enumerate(headlines, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   URL: {article['url']}")
        
        # Search for specific topic
        print("\n\n=== Searching for 'artificial intelligence' ===")
        ai_articles = fetcher.fetch_by_topic("artificial intelligence", days_back=3, max_results=3)
        for i, article in enumerate(ai_articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Published: {article['published_at']}")
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("Please set your NEWSAPI_KEY in the .env file")
    except Exception as e:
        print(f"\n❌ Error: {e}")
