# src/scrapers/substack_scraper.py - Substack-specific scraper

import logging
import re
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime

from .base_scraper import BaseScraper, ScrapedContent

logger = logging.getLogger(__name__)

class SubstackScraper(BaseScraper):
    """Specialized scraper for Substack newsletters"""
    
    def __init__(self, http_client, source_config: Dict):
        super().__init__(http_client, source_config)
    
    def extract_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract article URLs from Substack homepage or archive"""
        links = []
        
        # Substack-specific selectors for different page types
        if '/archive' in base_url:
            # Archive page selectors
            selectors = [
                'a[href*="/p/"]',  # Post URLs
                '.post-preview-title a',
                '.post-title a',
                '.post-item a',
                '.archive-item a',
                'h3 a',
                'h2 a',
                '.link-title'
            ]
        else:
            # Homepage selectors
            selectors = [
                'a[href*="/p/"]',  # Post URLs
                '.post-preview-title a',
                '.post-title a',
                'h3 a',
                'h2 a'
            ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href')
                if href and '/p/' in href:
                    absolute_url = self.make_absolute_url(href, base_url)
                    if self._is_valid_substack_url(absolute_url) and absolute_url not in links:
                        links.append(absolute_url)
        
        # Also look for any links that match Substack post pattern
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/p/' in href and 'substack.com' in href:
                absolute_url = self.make_absolute_url(href, base_url)
                if absolute_url not in links:
                    links.append(absolute_url)
        
        # Additional search for data attributes or JavaScript-loaded content
        for elem in soup.find_all(attrs={"data-href": True}):
            href = elem.get('data-href')
            if href and '/p/' in href:
                absolute_url = self.make_absolute_url(href, base_url)
                if self._is_valid_substack_url(absolute_url) and absolute_url not in links:
                    links.append(absolute_url)
        
        logger.info(f"Found {len(links)} potential Substack post links")
        return links[:20]  # Limit for performance
    
    def _is_valid_substack_url(self, url: str) -> bool:
        """Check if URL is a valid Substack post"""
        if not url or not isinstance(url, str):
            return False
        
        # Must be a Substack post URL
        return '/p/' in url and 'substack.com' in url
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> ScrapedContent:
        """Extract content from Substack post"""
        
        if not soup:
            logger.error("Soup is None in extract_content")
            return None
        
        try:
            content = ScrapedContent()
            
            # Extract title - Substack specific
            title_elem = soup.find('h1', class_=re.compile(r'post-title|headline')) or soup.find('h1')
            if title_elem:
                content.title = title_elem.get_text(strip=True)
            else:
                content.title = "Untitled Substack Post"
            
            # Extract author - look for byline
            author_elem = (
                soup.find(class_=re.compile(r'author|byline|writer')) or
                soup.find('a', href=re.compile(r'/profile/')) or 
                soup.select_one('.byline-names a')
            )
            if author_elem:
                content.author = author_elem.get_text(strip=True)
            
            # Extract date
            date_elem = (
                soup.find('time') or
                soup.find(class_=re.compile(r'date|published'))
            )
            if date_elem:
                try:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    from dateutil import parser
                    content.date = parser.parse(date_str)
                except:
                    pass
            
            # Extract main content - Substack specific selectors
            content_selectors = [
                '.available-content',
                '.body',
                '.post-content', 
                'article',
                '.markup'
            ]
            
            main_content = None
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    main_content = elem
                    break
            
            if not main_content:
                # Fallback: look for the largest text container
                main_content = self._find_largest_content_container(soup)
            
            if main_content:
                # Clean and convert to text
                content.content = self._extract_text_content(main_content)
                
                # Enhanced metadata
                content.metadata.update({
                    'scraped_at': datetime.now().isoformat(),
                    'word_count': len(content.content.split()) if content.content else 0,
                    'character_count': len(content.content) if content.content else 0,
                    'estimated_reading_time': max(1, len(content.content.split()) // 200) if content.content else 0,
                    'has_images': bool(main_content.find_all('img')) if main_content else False,
                    'source_type': 'substack',
                    'platform': 'substack'
                })
            else:
                logger.warning(f"No content found for {url}")
                return None
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting Substack content: {str(e)}")
            return None
    
    def _find_largest_content_container(self, soup: BeautifulSoup):
        """Find the largest content container as fallback"""
        
        candidates = []
        
        # Look for containers with substantial text
        for elem in soup.find_all(['div', 'section', 'article']):
            text = elem.get_text(strip=True)
            if len(text) > 500:  # Minimum content length
                score = len(text)
                
                # Bonus for typical content indicators
                if elem.find(['p', 'h1', 'h2', 'h3']):
                    score += 1000
                
                # Penalty for navigation-like content
                classes = ' '.join(elem.get('class', [])).lower()
                if any(word in classes for word in ['nav', 'menu', 'footer', 'sidebar']):
                    score -= 2000
                
                candidates.append((score, elem))
        
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        
        return None
    
    def _extract_text_content(self, element) -> str:
        """Extract clean text content from element"""
        
        # Remove unwanted elements
        for unwanted in element.find_all(['script', 'style', 'nav', 'footer']):
            unwanted.decompose()
        
        # Get text with some structure preservation
        text_content = ""
        
        for elem in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'blockquote']):
            text = elem.get_text(strip=True)
            if text:
                if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text_content += f"\n\n## {text}\n"
                elif elem.name == 'blockquote':
                    text_content += f"\n> {text}\n"
                else:
                    text_content += f"\n{text}\n"
        
        # Clean up excessive whitespace
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        return text_content.strip()


# Factory function
def create_substack_scraper(http_client, source_config):
    """Factory function to create Substack scraper"""
    return SubstackScraper(http_client, source_config)