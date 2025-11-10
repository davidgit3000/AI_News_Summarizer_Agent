"""
Web scraper module for fetching full article content from URLs.
Uses BeautifulSoup to extract article text when NewsAPI content is truncated.
"""

import logging
import requests
from typing import Optional, Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """Scrapes full article content from news URLs."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the web scraper.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logger.info("WebScraper initialized")
    
    def fetch_article_content(self, url: str) -> Dict[str, str]:
        """
        Fetch full article content from a URL.
        
        Args:
            url: Article URL
        
        Returns:
            Dictionary with 'content', 'status', and optional 'error'
        """
        try:
            # Make request
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # Try to extract article content using common patterns
            content = self._extract_article_text(soup, url)
            
            if content and len(content.strip()) > 100:
                logger.info(f"Successfully scraped {len(content)} chars from {urlparse(url).netloc}")
                return {
                    'content': content.strip(),
                    'status': 'success'
                }
            else:
                logger.warning(f"Insufficient content extracted from {url}")
                return {
                    'content': '',
                    'status': 'insufficient_content',
                    'error': 'Could not extract sufficient article content'
                }
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return {
                'content': '',
                'status': 'timeout',
                'error': 'Request timeout'
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"Access forbidden (403) for {url}")
                return {
                    'content': '',
                    'status': 'forbidden',
                    'error': 'Access forbidden - may require subscription'
                }
            elif e.response.status_code == 404:
                logger.warning(f"Article not found (404) for {url}")
                return {
                    'content': '',
                    'status': 'not_found',
                    'error': 'Article not found'
                }
            else:
                logger.warning(f"HTTP error {e.response.status_code} for {url}")
                return {
                    'content': '',
                    'status': 'http_error',
                    'error': f'HTTP {e.response.status_code}'
                }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                'content': '',
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_article_text(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extract article text using multiple strategies.
        
        Args:
            soup: BeautifulSoup object
            url: Original URL for domain-specific handling
        
        Returns:
            Extracted article text
        """
        domain = urlparse(url).netloc.lower()
        
        # Strategy 1: Try common article selectors
        article_selectors = [
            'article',
            '[role="article"]',
            '.article-content',
            '.article-body',
            '.post-content',
            '.entry-content',
            '.story-body',
            'main article',
            'main'
        ]
        
        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                # Get all paragraphs within the article
                paragraphs = article.find_all('p')
                if paragraphs:
                    text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                    if len(text) > 200:
                        return text
        
        # Strategy 2: Domain-specific selectors
        domain_selectors = {
            'wired.com': '.body__inner-container p, article p',
            'techcrunch.com': '.article-content p',
            'theverge.com': '.duet--article--article-body-component p',
            'cnn.com': '.article__content p',
            'bbc.com': '[data-component="text-block"] p, .ssrcss-1q0x1qg-Paragraph p',
            'reuters.com': '.article-body__content p',
        }
        
        for domain_key, selector in domain_selectors.items():
            if domain_key in domain:
                elements = soup.select(selector)
                if elements:
                    text = '\n\n'.join([el.get_text(strip=True) for el in elements if len(el.get_text(strip=True)) > 20])
                    if len(text) > 200:
                        return text
        
        # Strategy 3: Find all paragraphs with substantial text
        all_paragraphs = soup.find_all('p')
        substantial_paragraphs = [
            p.get_text(strip=True) 
            for p in all_paragraphs 
            if len(p.get_text(strip=True)) > 40
        ]
        
        if substantial_paragraphs:
            return '\n\n'.join(substantial_paragraphs)
        
        # Strategy 4: Fallback to all text
        return soup.get_text(separator='\n', strip=True)
    
    def is_content_truncated(self, content: str) -> bool:
        """
        Check if content appears to be truncated by NewsAPI.
        
        Args:
            content: Content string
        
        Returns:
            True if content appears truncated
        """
        if not content:
            return True
        
        # NewsAPI truncates content and adds [+X chars]
        truncation_indicators = [
            '[+',
            '…',
            '...',
            'Read more at',
            'Continue reading'
        ]
        
        # Check if content is very short or has truncation indicators
        if len(content) < 300:
            return True
        
        for indicator in truncation_indicators:
            if indicator in content[-100:]:  # Check last 100 chars
                return True
        
        return False


# Example usage
if __name__ == "__main__":
    scraper = WebScraper()
    
    # Test URLs
    test_urls = [
        "https://www.wired.com/story/what-is-adobe-firefly/",
        "https://techcrunch.com/2024/01/01/example-article/",
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print('='*60)
        
        result = scraper.fetch_article_content(url)
        
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Content length: {len(result['content'])} chars")
            print(f"Preview: {result['content'][:200]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown')}")
