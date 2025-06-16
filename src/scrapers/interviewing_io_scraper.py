# src/scrapers/interviewing_io_scraper.py - Enhanced interviewing.io scraper with comprehensive link extraction

import logging
from typing import List
from bs4 import BeautifulSoup
from datetime import datetime
import re

from .base_scraper import BaseScraper, ScrapedContent

logger = logging.getLogger(__name__)

class InterviewingIOScraper(BaseScraper):
    """Enhanced scraper for interviewing.io with comprehensive link extraction"""
    
    def extract_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract ALL article URLs from interviewing.io with enhanced patterns"""
        links = []
        
        # Enhanced selectors for maximum coverage
        link_selectors = [
            # Blog post links
            'a[href*="/blog/"]',
            'a[href*="/post/"]',
            'a[href*="/article/"]',
            
            # Title and heading links
            '.post-title a',
            '.entry-title a',
            '.article-title a',
            'h1 a', 'h2 a', 'h3 a', 'h4 a',
            
            # Card and container links
            '.card a[href*="/blog/"]',
            '.article a[href*="/blog/"]',
            '.post a[href*="/blog/"]',
            '.entry a[href*="/blog/"]',
            
            # List item links
            'li a[href*="/blog/"]',
            'ul a[href*="/blog/"]',
            
            # Generic blog patterns
            'a[href*="interview"]',
            'a[href*="guide"]',
            'a[href*="tips"]',
            'a[href*="how-to"]',
            'a[href*="why-"]',
            'a[href*="what-"]',
            
            # Specific interviewing.io patterns
            'a[href*="hiring"]',
            'a[href*="recruiter"]',
            'a[href*="resume"]',
            'a[href*="coding"]',
            'a[href*="technical"]',
            'a[href*="salary"]',
            'a[href*="negotiation"]',
            'a[href*="outreach"]',
            
            # Company and topic guides
            'a[href*="/companies/"]',
            'a[href*="/topics/"]',
            'a[href*="/learn/"]',
            
            # Fallback: any internal link that looks like content
            'a[href^="/"][href*="-"]',  # Internal links with hyphens
        ]
        
        found_links = set()  # Use set to avoid duplicates
        
        for selector in link_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href and self._is_valid_content_link(href, base_url):
                        absolute_url = self.make_absolute_url(href, base_url)
                        found_links.add(absolute_url)
            except Exception as e:
                logger.debug(f"Link selector '{selector}' failed: {str(e)}")
        
        # Convert back to list and sort for consistency
        links = sorted(list(found_links))
        
        # Additional pattern matching for missed links
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href and self._is_content_url_pattern(href):
                absolute_url = self.make_absolute_url(href, base_url)
                if absolute_url not in links:
                    links.append(absolute_url)
        
        logger.info(f"Found {len(links)} potential article links")
        
        # Log sample links for debugging
        if links:
            logger.debug("Sample links found:")
            for i, link in enumerate(links[:5]):
                logger.debug(f"  {i+1}. {link}")
        
        return links
    
    def _is_valid_content_link(self, href: str, base_url: str) -> bool:
        """Check if a link is likely to be a valid content page"""
        if not href:
            return False
        
        # Skip non-content links
        skip_patterns = [
            'mailto:', 'tel:', 'javascript:', '#',
            '/contact', '/about', '/privacy', '/terms',
            '/login', '/signup', '/register', '/auth',
            '.pdf', '.doc', '.zip', '.jpg', '.png', '.gif',
            '/api/', '/admin/', '/wp-admin/',
            'facebook.com', 'twitter.com', 'linkedin.com',
            'youtube.com', 'instagram.com'
        ]
        
        href_lower = href.lower()
        for pattern in skip_patterns:
            if pattern in href_lower:
                return False
        
        # Must be internal or from same domain
        if href.startswith('http') and base_url not in href:
            return False
        
        # Must look like a content URL
        return self._is_content_url_pattern(href)
    
    def _is_content_url_pattern(self, href: str) -> bool:
        """Check if URL pattern suggests it's a content page"""
        
        # Content indicators
        content_patterns = [
            '/blog/', '/post/', '/article/', '/guide/',
            '/learn/', '/tutorial/', '/tips/',
            'interview', 'hiring', 'recruiter', 'resume',
            'coding', 'technical', 'salary', 'negotiation',
            'how-to', 'why-', 'what-', 'best-',
            'meta', 'google', 'amazon', 'microsoft',
            'faang', 'startup', 'engineer'
        ]
        
        href_lower = href.lower()
        for pattern in content_patterns:
            if pattern in href_lower:
                return True
        
        # Check for hyphenated URLs (common for blog posts)
        if href.count('-') >= 2:
            return True
        
        return False
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> ScrapedContent:
        """Extract content from interviewing.io article page"""
        content = ScrapedContent()
        
        # Extract title with more selectors
        title_selectors = [
            'h1.post-title',
            'h1.entry-title', 
            'h1.article-title',
            '.title h1',
            'h1',
            '.post-title',
            '.entry-title',
            '.article-title',
            'title'
        ]
        content.title = self.extract_text_by_selectors(soup, title_selectors)
        
        # Clean title
        if content.title:
            content.title = re.sub(r'\s+', ' ', content.title).strip()
            # Remove site name from title if present
            content.title = re.sub(r'\s*[\-\|]\s*interviewing\.io.*$', '', content.title, flags=re.IGNORECASE)
        
        # Extract author with more patterns
        author_selectors = [
            '.author-name',
            '.byline-author',
            '.post-author a',
            '.entry-author a',
            '[rel="author"]',
            '.author',
            '.byline',
            '.post-author',
            '.entry-author'
        ]
        content.author = self.extract_text_by_selectors(soup, author_selectors)
        
        # Extract date
        content.date = self._extract_date(soup)
        
        # Extract main content
        content.content = self._extract_main_content(soup)
        
        # Enhanced metadata
        if content.content:
            word_count = len(content.content.split())
            content.metadata.update({
                'word_count': word_count,
                'character_count': len(content.content),
                'estimated_reading_time': max(1, word_count // 200),
                'has_code_blocks': bool(re.search(r'```|<pre|<code', content.content)),
                'has_images': bool(soup.find('img')),
                'has_links': bool(re.search(r'\[.*\]\(.*\)|<a.*href', content.content)),
                'paragraph_count': content.content.count('\n\n') + 1,
                'source_type': 'interviewing_io',
                'scraped_at': datetime.now().isoformat(),
                'content_hash': str(hash(content.content))[:16] if content.content else None
            })
        
        return content
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Enhanced main content extraction"""
        
        # Remove unwanted elements comprehensively
        unwanted_selectors = [
            'nav', 'header', 'footer', 'aside',
            '.sidebar', '.navigation', '.menu', '.nav',
            '.social-share', '.share', '.comments', '.related-posts',
            '.advertisement', '.ads', '.popup', '.modal',
            '.cookie-notice', '.newsletter', '.signup',
            'script', 'style', 'noscript', 'iframe',
            '.breadcrumb', '.pagination', '.tags',
            '.metadata', '.post-meta', '.entry-meta'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Enhanced content selectors
        content_selectors = [
            '.post-content .content',
            '.entry-content .content',
            '.article-content .content',
            '.post-content',
            '.entry-content', 
            '.article-content',
            '.content-area',
            '.main-content',
            '.content',
            'article .content',
            'article',
            '#content',
            '.post-body',
            '.entry-body',
            '.article-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content_text = self._extract_formatted_text(content_elem)
                if len(content_text.strip()) > 200:  # Must have substantial content
                    logger.debug(f"Content extracted using selector: {selector}")
                    return content_text
        
        # Fallback: extract from body but filter out navigation/footer
        body = soup.find('body')
        if body:
            # Remove navigation and footer elements
            for nav in body.find_all(['nav', 'header', 'footer']):
                nav.decompose()
            
            content_text = self._extract_formatted_text(body)
            if len(content_text.strip()) > 200:
                logger.debug("Content extracted from body (fallback)")
                return content_text
        
        # Last resort: get all text
        all_text = soup.get_text(separator=' ', strip=True)
        logger.warning("Using last resort text extraction")
        return all_text
    
    def _extract_formatted_text(self, element) -> str:
        """Extract text while preserving basic formatting"""
        
        # Convert common elements to markdown-like format
        # Handle code blocks
        for code in element.find_all(['pre', 'code']):
            if code.name == 'pre':
                code.string = f"\n```\n{code.get_text()}\n```\n"
            else:
                code.string = f"`{code.get_text()}`"
        
        # Handle headings
        for i in range(1, 7):
            for heading in element.find_all(f'h{i}'):
                heading.string = f"\n{'#' * i} {heading.get_text()}\n"
        
        # Handle lists
        for ul in element.find_all('ul'):
            for li in ul.find_all('li'):
                li.string = f"- {li.get_text()}\n"
        
        for ol in element.find_all('ol'):
            for i, li in enumerate(ol.find_all('li'), 1):
                li.string = f"{i}. {li.get_text()}\n"
        
        # Handle paragraphs
        for p in element.find_all('p'):
            p.string = f"{p.get_text()}\n\n"
        
        # Handle line breaks
        for br in element.find_all('br'):
            br.replace_with('\n')
        
        # Extract final text
        text = element.get_text(separator=' ')
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Collapse multiple spaces
        
        return text.strip()
    
    def _extract_date(self, soup: BeautifulSoup) -> datetime:
        """Extract publication date from the page"""
        
        date_selectors = [
            'time[datetime]',
            '.date',
            '.published',
            '.post-date',
            '.entry-date',
            '[datetime]'
        ]
        
        for selector in date_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    # Try datetime attribute first
                    datetime_attr = element.get('datetime')
                    if datetime_attr:
                        return self._parse_date_string(datetime_attr)
                    
                    # Try text content
                    date_text = element.get_text(strip=True)
                    if date_text:
                        return self._parse_date_string(date_text)
            except Exception as e:
                logger.debug(f"Date selector '{selector}' failed: {str(e)}")
        
        # Fallback: look in meta tags
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="publishdate"]'
        ]
        
        for selector in meta_selectors:
            try:
                meta = soup.select_one(selector)
                if meta:
                    content = meta.get('content')
                    if content:
                        return self._parse_date_string(content)
            except Exception as e:
                logger.debug(f"Meta selector '{selector}' failed: {str(e)}")
        
        return None
    
    def _parse_date_string(self, date_str: str) -> datetime:
        """Parse various date string formats"""
        if not date_str:
            return None
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%dT%H:%M:%S%z',  # ISO format with timezone
            '%Y-%m-%dT%H:%M:%S',    # ISO format without timezone
            '%Y-%m-%d %H:%M:%S',    # Standard format
            '%Y-%m-%d',             # Date only
            '%B %d, %Y',            # "January 1, 2023"
            '%b %d, %Y',            # "Jan 1, 2023"
            '%d %B %Y',             # "1 January 2023"
            '%d %b %Y',             # "1 Jan 2023"
        ]
        
        # Clean the date string
        date_str = date_str.strip()
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None


# Factory function
def create_interviewing_io_scraper(http_client, source_config):
    """Factory function to create interviewing.io scraper"""
    return InterviewingIOScraper(http_client, source_config)
