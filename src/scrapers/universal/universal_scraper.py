"""
Universal Web Scraper

A robust scraper that can handle ANY website including:
- Blog sites (WordPress, custom CMS)
- Substack platforms
- Documentation sites
- News sites
- Technical content sites

This scraper automatically detects content patterns and extracts articles.
"""

import re
import time
import logging
from typing import List, Set, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass
from datetime import datetime

from ..base_scraper import ScrapedContent


@dataclass
class ContentQuality:
    """Content quality metrics"""
    word_count: int
    paragraph_count: int
    code_blocks: int
    links: int
    images: int
    headers: int
    quality_score: float


class UniversalWebScraper:
    """Universal scraper that works on any website"""
    
    def __init__(self, http_client, config: dict):
        self.client = http_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.scraped_urls = set()
        self.failed_urls = set()
        
        # Content quality thresholds
        self.min_word_count = config.get('min_word_count', 200)
        self.min_quality_score = config.get('min_quality_score', 0.3)
        
    def scrape_website(self, base_url: str, max_pages: int = None) -> List[ScrapedContent]:
        """
        Scrape an entire website automatically
        
        Args:
            base_url: The website to scrape
            max_pages: Maximum number of pages to scrape (None = unlimited)
            
        Returns:
            List of scraped content
        """
        self.logger.info(f"🌐 Starting universal scrape of: {base_url}")
        
        try:
            # Detect website type and strategy
            website_type = self._detect_website_type(base_url)
            self.logger.info(f"🔍 Detected website type: {website_type}")
            
            # Get all article links
            article_links = self._discover_all_articles(base_url, website_type)
            self.logger.info(f"📊 Found {len(article_links)} potential articles")
            
            # Limit pages if specified
            if max_pages:
                article_links = article_links[:max_pages]
                self.logger.info(f"📝 Limited to {max_pages} pages")
            
            # Scrape each article
            scraped_content = []
            for i, link in enumerate(article_links, 1):
                if link not in self.scraped_urls:
                    self.logger.info(f"📄 Scraping article {i}/{len(article_links)}: {link}")
                    
                    content = self._scrape_single_article(link, website_type)
                    if content and self._is_quality_content(content):
                        scraped_content.append(content)
                        self.logger.debug(f"✅ Quality content: {content.title[:50]}...")
                    else:
                        self.logger.debug(f"❌ Low quality content skipped: {link}")
                    
                    time.sleep(0.5)  # Be respectful
                else:
                    self.logger.debug(f"🔄 Already scraped: {link}")
            
            self.logger.info(f"✅ Universal scrape complete: {len(scraped_content)} quality articles")
            return scraped_content
            
        except Exception as e:
            self.logger.error(f"❌ Universal scrape failed for {base_url}: {str(e)}")
            return []
    
    def _detect_website_type(self, url: str) -> str:
        """Detect the type of website for optimal scraping strategy"""
        
        domain = urlparse(url).netloc.lower()
        
        # Substack detection
        if 'substack.com' in domain:
            return 'substack'
        
        # Common blog platforms
        if any(platform in domain for platform in ['wordpress', 'medium', 'ghost', 'blogger']):
            return 'blog_platform'
        
        # Technical sites
        if any(tech in domain for tech in ['github.io', 'readthedocs', 'gitbook']):
            return 'documentation'
        
        # Check page content for more clues
        try:
            soup = self._get_soup(url)
            if soup:
                # Check for common CMS indicators
                if soup.find('meta', {'name': 'generator', 'content': re.compile('WordPress', re.I)}):
                    return 'wordpress'
                if soup.find('meta', {'name': 'generator', 'content': re.compile('Ghost', re.I)}):
                    return 'ghost'
                if soup.select('.substack'):
                    return 'substack'
                if soup.select('article') or soup.select('.post') or soup.select('.entry'):
                    return 'blog'
        except:
            pass
        
        return 'generic'
    
    def _discover_all_articles(self, base_url: str, website_type: str) -> List[str]:
        """Discover all article links on a website"""
        
        discovered_links = set()
        pages_to_check = [base_url]
        checked_pages = set()
        
        # Strategy based on website type
        if website_type == 'substack':
            pages_to_check.extend([
                f"{base_url.rstrip('/')}/archive",
                f"{base_url.rstrip('/')}/archive?sort=new"
            ])
        
        while pages_to_check and len(checked_pages) < 20:  # Limit discovery pages
            current_page = pages_to_check.pop(0)
            if current_page in checked_pages:
                continue
                
            checked_pages.add(current_page)
            self.logger.debug(f"🔍 Discovering links on: {current_page}")
            
            soup = self._get_soup(current_page)
            if not soup:
                continue
            
            # Extract article links based on website type
            new_links = self._extract_article_links(soup, current_page, website_type)
            discovered_links.update(new_links)
            
            # Find pagination links
            pagination_links = self._find_pagination_links(soup, current_page, website_type)
            pages_to_check.extend(pagination_links)
        
        return list(discovered_links)
    
    def _extract_article_links(self, soup: BeautifulSoup, base_url: str, website_type: str) -> Set[str]:
        """Extract article links using multiple strategies"""
        
        links = set()
        domain = urlparse(base_url).netloc
        
        # Universal selectors that work on most sites
        selectors = [
            # Common article link patterns
            'a[href*="/blog/"]',
            'a[href*="/post/"]',
            'a[href*="/article/"]',
            'a[href*="/p/"]',  # Substack
            'a[href*="/entry/"]',
            
            # Content container selectors
            'article a[href]',
            '.post a[href]',
            '.entry a[href]',
            '.blog-post a[href]',
            '.content a[href]',
            
            # Title selectors
            'h1 a[href]', 'h2 a[href]', 'h3 a[href]',
            '.title a[href]',
            '.post-title a[href]',
            '.entry-title a[href]',
            '.article-title a[href]',
            
            # Substack specific
            '.post-preview-title a[href]',
            '.pencraft a[href]',
            
            # Generic content links
            '[class*="title"] a[href]',
            '[class*="headline"] a[href]',
            '[class*="post"] a[href]',
            '[class*="article"] a[href]'
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if self._is_valid_article_url(full_url, domain, website_type):
                            links.add(full_url)
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
        
        return links
    
    def _find_pagination_links(self, soup: BeautifulSoup, base_url: str, website_type: str) -> List[str]:
        """Find pagination and archive links"""
        
        pagination_links = []
        
        # Common pagination selectors
        pagination_selectors = [
            'a[href*="page/"]',
            'a[href*="page="]',
            '.pagination a[href]',
            '.pager a[href]',
            '.nav-links a[href]',
            'a[rel="next"]',
            'a[class*="next"]',
            'a[class*="more"]'
        ]
        
        if website_type == 'substack':
            pagination_selectors.extend([
                'a[href*="archive"]',
                'a[href*="offset="]'
            ])
        
        for selector in pagination_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if self._is_valid_pagination_url(full_url, base_url):
                            pagination_links.append(full_url)
            except:
                pass
        
        return pagination_links
    
    def _is_valid_article_url(self, url: str, domain: str, website_type: str) -> bool:
        """Check if URL looks like an article"""
        
        if not url or url in self.scraped_urls or url in self.failed_urls:
            return False
        
        # Must be from same domain
        if domain not in url:
            return False
        
        # Exclude common non-article patterns
        exclude_patterns = [
            'login', 'register', 'signup', 'subscribe', 'privacy', 'terms',
            'contact', 'about', 'author', 'tag/', 'category/', 'search',
            '.pdf', '.jpg', '.png', '.gif', '.css', '.js',
            'feed', 'rss', 'xml', 'sitemap',
            'mailto:', 'tel:', '#', 'javascript:',
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com'
        ]
        
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # Substack specific validation
        if website_type == 'substack':
            return '/p/' in url and not any(x in url for x in ['/comments', '/edit'])
        
        # Blog specific patterns
        if website_type in ['blog', 'wordpress', 'ghost']:
            article_indicators = ['/blog/', '/post/', '/article/', '/entry/']
            return any(indicator in url for indicator in article_indicators)
        
        # Generic validation - look for year patterns or specific paths
        if re.search(r'/\d{4}/', url) or any(pattern in url for pattern in ['/blog/', '/post/', '/article/']):
            return True
        
        # If URL has meaningful path segments (not just domain)
        path = urlparse(url).path
        if path and len(path.strip('/').split('/')) >= 1 and not path.endswith('/'):
            return True
        
        return False
    
    def _is_valid_pagination_url(self, url: str, base_url: str) -> bool:
        """Check if URL is valid pagination"""
        
        if not url or url == base_url:
            return False
        
        # Must be from same domain
        if urlparse(base_url).netloc not in url:
            return False
        
        # Look for pagination indicators
        pagination_indicators = ['page/', 'page=', 'offset=', 'p=', 'archive']
        return any(indicator in url for indicator in pagination_indicators)
    
    def _scrape_single_article(self, url: str, website_type: str) -> Optional[ScrapedContent]:
        """Scrape a single article with website-specific optimizations"""
        
        try:
            self.scraped_urls.add(url)
            
            soup = self._get_soup(url)
            if not soup:
                self.failed_urls.add(url)
                return None
            
            # Extract content using multiple strategies
            title = self._extract_title(soup, website_type)
            content = self._extract_content(soup, website_type)
            author = self._extract_author(soup, website_type)
            
            if not title or not content:
                self.failed_urls.add(url)
                return None
            
            # Create content object
            scraped_content = ScrapedContent()
            scraped_content.title = title
            scraped_content.content = content
            scraped_content.source_url = url
            scraped_content.author = author
            scraped_content.metadata = {
                'content_type': self._determine_content_type(url, website_type),
                'website_type': website_type,
                'scraped_at': datetime.now().isoformat(),
                'word_count': len(content.split()),
                'quality_metrics': self._calculate_quality_metrics(content)
            }
            
            return scraped_content
            
        except Exception as e:
            self.logger.debug(f"Error scraping {url}: {str(e)}")
            self.failed_urls.add(url)
            return None
    
    def _extract_title(self, soup: BeautifulSoup, website_type: str) -> Optional[str]:
        """Extract title using multiple fallback strategies"""
        
        # Website-specific title extraction
        if website_type == 'substack':
            title_selectors = [
                'h1.post-title',
                'h1.pencraft',
                '.post-header h1',
                'h1[class*="title"]'
            ]
        else:
            title_selectors = [
                'h1.post-title',
                'h1.entry-title',
                'h1.article-title',
                '.post-header h1',
                '.entry-header h1',
                'article h1',
                'h1',
                'title'
            ]
        
        for selector in title_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    if title and 3 < len(title) < 200:
                        return title
            except:
                continue
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup, website_type: str) -> Optional[str]:
        """Extract main content using multiple strategies"""
        
        # Remove unwanted elements
        for unwanted in soup.select('nav, footer, header, aside, .sidebar, .navigation, .comments, .social-share, script, style, .advertisement, .ads'):
            unwanted.decompose()
        
        # Website-specific content extraction
        if website_type == 'substack':
            content_selectors = [
                '.available-content',
                '.body',
                '.post-content',
                'article .content',
                '.pencraft'
            ]
        else:
            content_selectors = [
                '.post-content',
                '.entry-content',
                '.article-content',
                '.content',
                'main article',
                'article .body',
                '.post-body',
                '[class*="content"]',
                '.story-body'
            ]
        
        for selector in content_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    content = self._clean_content(element.get_text(separator='\n', strip=True))
                    if content and len(content) > self.min_word_count:
                        return content
            except:
                continue
        
        # Fallback to main content areas
        fallback_selectors = ['main', 'article', '.main', '#main', '#content']
        for selector in fallback_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    content = self._clean_content(element.get_text(separator='\n', strip=True))
                    if content and len(content) > 100:
                        return content
            except:
                continue
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup, website_type: str) -> Optional[str]:
        """Extract author information"""
        
        if website_type == 'substack':
            author_selectors = [
                '.pencraft.pc-display-flex.pc-gap-4.pc-reset .pencraft',
                '.publication-logo + div',
                '[class*="author"]'
            ]
        else:
            author_selectors = [
                '.author',
                '.byline',
                '[rel="author"]',
                '.post-author',
                '.entry-author',
                '[class*="author"]',
                '.written-by'
            ]
        
        for selector in author_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    author = element.get_text(strip=True)
                    if author and len(author) < 100:
                        return author
            except:
                continue
        
        return None
    
    def _determine_content_type(self, url: str, website_type: str) -> str:
        """Determine content type based on URL and website type"""
        
        if website_type == 'substack':
            return 'blog'  # Substack posts are essentially blog posts
        
        if 'interview' in url.lower():
            return 'interview_guide'
        
        if any(guide_indicator in url.lower() for guide_indicator in ['guide', 'tutorial', 'how-to']):
            return 'guide'
        
        return 'blog'
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'Subscribe to.*?newsletter',
            r'Follow us on.*?social',
            r'Share this.*?post',
            r'Leave a comment',
            r'Tags:.*?$',
            r'Categories:.*?$'
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content.strip()
    
    def _calculate_quality_metrics(self, content: str) -> Dict:
        """Calculate content quality metrics"""
        
        if not content:
            return {'quality_score': 0.0}
        
        word_count = len(content.split())
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        code_blocks = content.count('```') + content.count('    ')
        links = content.count('http')
        headers = len(re.findall(r'^#+\s+', content, re.MULTILINE))
        
        # Calculate quality score
        quality_score = 0.0
        
        # Word count factor
        if word_count > 500:
            quality_score += 0.3
        elif word_count > 200:
            quality_score += 0.2
        
        # Structure factors
        if paragraph_count > 3:
            quality_score += 0.2
        if headers > 0:
            quality_score += 0.1
        if code_blocks > 0:
            quality_score += 0.2
        
        # Technical content indicators
        technical_keywords = ['algorithm', 'code', 'programming', 'technical', 'interview', 'data structure']
        if any(keyword in content.lower() for keyword in technical_keywords):
            quality_score += 0.2
        
        return {
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'code_blocks': code_blocks,
            'links': links,
            'headers': headers,
            'quality_score': min(1.0, quality_score)
        }
    
    def _is_quality_content(self, content: ScrapedContent) -> bool:
        """Check if content meets quality standards"""
        
        if not content or not content.content:
            return False
        
        word_count = len(content.content.split())
        quality_score = content.metadata.get('quality_metrics', {}).get('quality_score', 0.0)
        
        return (word_count >= self.min_word_count and 
                quality_score >= self.min_quality_score)
    
    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object for URL with error handling"""
        
        try:
            response = self.client.get(url, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            else:
                self.logger.debug(f"HTTP {response.status_code} for {url}")
        except Exception as e:
            self.logger.debug(f"Failed to get {url}: {str(e)}")
        
        return None
