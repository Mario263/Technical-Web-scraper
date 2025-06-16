# src/scrapers/base_scraper.py - Base class for all scrapers

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapedContent:
    """Data class for scraped content"""
    
    def __init__(self):
        self.title: str = ""
        self.content: str = ""
        self.author: str = ""
        self.date: Optional[datetime] = None
        self.source_url: str = ""
        self.raw_html: str = ""
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "date": self.date.isoformat() if self.date else None,
            "source_url": self.source_url,
            "metadata": self.metadata
        }
    
    def is_valid(self) -> bool:
        """Check if content is valid"""
        return bool(self.title and self.content and len(self.content.strip()) > 50)


class BaseScraper(ABC):
    """Base class for all content scrapers"""
    
    def __init__(self, http_client, source_config: Dict):
        self.http_client = http_client
        self.source_config = source_config
        self.scraped_count = 0
        self.failed_count = 0
    
    @abstractmethod
    def extract_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract article URLs from listing page"""
        pass
    
    @abstractmethod
    def extract_content(self, soup: BeautifulSoup, url: str) -> ScrapedContent:
        """Extract content from individual article page"""
        pass
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get and parse page content"""
        try:
            response = self.http_client.get(url)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'lxml')
            else:
                logger.error(f"Failed to fetch {url}: Status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception fetching {url}: {str(e)}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Basic text cleaning
        text = text.strip()
        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text
    
    def extract_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Try multiple CSS selectors to extract text"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return self.clean_text(text)
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {str(e)}")
                continue
        return ""
    
    def make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URL to absolute URL"""
        return urljoin(base_url, url)
    
    def is_valid_article_url(self, url: str) -> bool:
        """Check if URL looks like a valid article"""
        if not url:
            return False
        
        # Skip common non-article URLs
        skip_patterns = [
            '/tag/', '/category/', '/author/', '/page/',
            '#', 'javascript:', 'mailto:', 'tel:',
            '.pdf', '.doc', '.jpg', '.png', '.gif'
        ]
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        return True
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def scrape_listing_page(self, url: str) -> List[str]:
        """Scrape listing page for article URLs"""
        logger.info(f"Scraping listing page: {url}")
        
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        article_links = self.extract_article_links(soup, url)
        valid_links = [link for link in article_links if self.is_valid_article_url(link)]
        
        logger.info(f"Found {len(valid_links)} valid article links from {url}")
        return valid_links
    
    def scrape_article(self, url: str) -> Optional[ScrapedContent]:
        """Scrape individual article"""
        logger.info(f"Scraping article: {url}")
        
        soup = self.get_page_content(url)
        if not soup:
            self.failed_count += 1
            return None
        
        try:
            content = self.extract_content(soup, url)
            content.source_url = url
            content.metadata['content_hash'] = self.generate_content_hash(content.content)
            content.metadata['scraped_at'] = datetime.now().isoformat()
            
            if content.is_valid():
                self.scraped_count += 1
                logger.info(f"Successfully scraped: {content.title[:50]}...")
                return content
            else:
                logger.warning(f"Invalid content from {url}")
                self.failed_count += 1
                return None
                
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            self.failed_count += 1
            return None
    
    def scrape_source(self, max_articles: int = 50) -> List[ScrapedContent]:
        """Scrape all articles from source"""
        logger.info(f"Starting to scrape source: {self.source_config.get('base_url')}")
        
        base_url = self.source_config['base_url']
        
        # Get article links
        article_links = self.scrape_listing_page(base_url)
        
        if not article_links:
            logger.warning(f"No article links found for {base_url}")
            return []
        
        # Limit articles if specified
        if max_articles > 0:
            article_links = article_links[:max_articles]
        
        # Scrape articles
        scraped_articles = []
        for link in article_links:
            content = self.scrape_article(link)
            if content:
                scraped_articles.append(content)
        
        logger.info(f"Scraping complete. Success: {self.scraped_count}, Failed: {self.failed_count}")
        return scraped_articles
    
    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics"""
        return {
            "scraped_count": self.scraped_count,
            "failed_count": self.failed_count,
            "total_attempted": self.scraped_count + self.failed_count
        }