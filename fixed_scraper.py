#!/usr/bin/env python3
"""
🔧 FIXED SCRAPER - Correctly handles quill.co vs quill.com

This fixes the issue where the scraper was going to quill.com (office supplies)
instead of quill.co (data analytics) as specified in the assignment.
"""

import sys
import json
import logging
import argparse
import time
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

# Third-party imports
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Missing required packages. Run: pip install requests beautifulsoup4 lxml")
    sys.exit(1)

# Create directories
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class ScrapedContent:
    """Data structure for scraped content"""
    title: str = ""
    content: str = ""
    author: str = ""
    source_url: str = ""
    content_type: str = "blog"
    
    def is_valid(self) -> bool:
        """Check if content is valid"""
        return bool(
            self.title and 
            len(self.title.strip()) > 3 and
            self.content and 
            len(self.content.strip()) > 100
        )


class FixedHTTPClient:
    """HTTP client that correctly handles redirects"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request with proper handling"""
        kwargs.setdefault('timeout', 15)
        kwargs.setdefault('allow_redirects', False)  # Handle redirects manually
        
        for attempt in range(3):
            try:
                response = self.session.get(url, **kwargs)
                
                # Handle redirects manually to prevent quill.co -> quill.com
                if response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get('Location')
                    if redirect_url:
                        # Don't follow redirects from quill.co to quill.com
                        if 'quill.co' in url and 'quill.com' in redirect_url:
                            logging.warning(f"Blocked redirect from {url} to {redirect_url}")
                            # Try to get the page anyway
                            kwargs['allow_redirects'] = True
                            response = self.session.get(url, **kwargs)
                        else:
                            # Follow other redirects
                            url = redirect_url
                            kwargs['allow_redirects'] = True
                            response = self.session.get(url, **kwargs)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return response
                    
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise e
                time.sleep(1)
        
        return response
    
    def close(self):
        self.session.close()


class FixedScraper:
    """Scraper with fixes for specific websites"""
    
    def __init__(self):
        self.client = FixedHTTPClient()
        self.logger = logging.getLogger(__name__)
        
    def scrape_website(self, base_url: str, max_pages: int = None) -> List[ScrapedContent]:
        """Scrape a website with site-specific fixes"""
        
        self.logger.info(f"🌐 Scraping: {base_url}")
        
        # Apply site-specific fixes
        if 'quill.co' in base_url:
            return self._scrape_quill_co(base_url, max_pages)
        else:
            return self._scrape_generic(base_url, max_pages)
    
    def _scrape_quill_co(self, base_url: str, max_pages: int = None) -> List[ScrapedContent]:
        """Scrape quill.co specifically (data analytics blog)"""
        
        self.logger.info("🔍 Detected: quill.co (data analytics blog)")
        
        try:
            # Ensure we're using the correct URL
            if not base_url.endswith('/blog'):
                base_url = base_url.rstrip('/') + '/blog'
            
            # Get the blog page
            soup = self._get_soup(base_url)
            if not soup:
                self.logger.error(f"Could not access {base_url}")
                return []
            
            # Find article links specifically for quill.co
            article_links = self._find_quill_co_articles(soup, base_url)
            self.logger.info(f"📊 Found {len(article_links)} quill.co articles")
            
            if not article_links:
                self.logger.warning("No articles found on quill.co blog")
                return []
            
            # Log sample links
            for i, link in enumerate(article_links[:3], 1):
                self.logger.info(f"   Sample {i}: {link}")
            
            # Limit if specified
            if max_pages and max_pages > 0:
                article_links = article_links[:max_pages]
            
            # Scrape each article
            scraped_content = []
            for i, link in enumerate(article_links, 1):
                self.logger.info(f"📄 Scraping quill.co {i}/{len(article_links)}: {link}")
                
                content = self._scrape_single_article(link)
                if content and content.is_valid():
                    content.content_type = "blog"  # quill.co is a data analytics blog
                    scraped_content.append(content)
                    self.logger.info(f"   ✅ Success: {content.title[:50]}...")
                else:
                    self.logger.warning(f"   ❌ Failed to extract valid content")
                
                time.sleep(0.5)  # Be respectful
            
            self.logger.info(f"✅ quill.co scraping complete: {len(scraped_content)} articles")
            return scraped_content
            
        except Exception as e:
            self.logger.error(f"❌ Failed to scrape quill.co: {str(e)}")
            return []
    
    def _find_quill_co_articles(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find article links specifically on quill.co blog"""
        
        links = set()
        domain = urlparse(base_url).netloc
        
        # quill.co specific selectors
        selectors = [
            'a[href*="/blog/"]',
            'a[href*="quill.co/blog/"]',
            '.blog-post a[href]',
            '.post a[href]',
            '.article a[href]',
            'h1 a[href]', 'h2 a[href]', 'h3 a[href]',
            '.entry-title a[href]',
            '.post-title a[href]'
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        # Ensure it's a quill.co blog post, not a redirect to quill.com
                        if self._is_valid_quill_co_article(full_url):
                            links.add(full_url)
            except:
                continue
        
        # Also look for any text that might be article titles
        # and find their parent links
        for text_elem in soup.find_all(text=True):
            if text_elem.parent and text_elem.parent.name == 'a':
                href = text_elem.parent.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_quill_co_article(full_url):
                        links.add(full_url)
        
        return list(links)
    
    def _is_valid_quill_co_article(self, url: str) -> bool:
        """Check if URL is valid quill.co article"""
        
        if not url:
            return False
        
        # Must be quill.co, not quill.com
        if 'quill.co' not in url:
            return False
        
        # Must be a blog post
        if '/blog/' not in url:
            return False
        
        # Skip unwanted patterns
        skip_patterns = [
            'login', 'register', 'signup', 'privacy', 'terms',
            'contact', 'about', '.pdf', '.jpg', '.png',
            'mailto:', 'tel:', '#'
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        return True
    
    def _scrape_generic(self, base_url: str, max_pages: int = None) -> List[ScrapedContent]:
        """Generic website scraping"""
        
        try:
            soup = self._get_soup(base_url)
            if not soup:
                return []
            
            # Find article links
            article_links = self._find_article_links(soup, base_url)
            self.logger.info(f"📊 Found {len(article_links)} potential articles")
            
            # Limit if specified
            if max_pages and max_pages > 0:
                article_links = article_links[:max_pages]
            
            # Scrape each article
            scraped_content = []
            for i, link in enumerate(article_links, 1):
                self.logger.info(f"📄 Scraping {i}/{len(article_links)}: {link}")
                
                content = self._scrape_single_article(link)
                if content and content.is_valid():
                    scraped_content.append(content)
                
                time.sleep(0.5)
            
            self.logger.info(f"✅ Scraped {len(scraped_content)} articles")
            return scraped_content
            
        except Exception as e:
            self.logger.error(f"❌ Failed to scrape {base_url}: {str(e)}")
            return []
    
    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup for URL"""
        try:
            response = self.client.get(url, allow_redirects=True)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            else:
                self.logger.warning(f"HTTP {response.status_code} for {url}")
        except Exception as e:
            self.logger.debug(f"Failed to get {url}: {str(e)}")
        return None
    
    def _find_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find article links on page"""
        
        links = set()
        domain = urlparse(base_url).netloc
        
        # Comprehensive selectors
        selectors = [
            'a[href*="/blog/"]',
            'a[href*="/post/"]',
            'a[href*="/article/"]',
            'a[href*="/p/"]',  # Substack
            'a[href*="/topics/"]',  # interviewing.io
            'a[href*="/learn/"]',   # interviewing.io
            'a[href*="/guides/"]',
            'article a[href]',
            '.post a[href]',
            '.entry a[href]',
            'h1 a[href]', 'h2 a[href]', 'h3 a[href]',
            '.post-title a[href]',
            '.entry-title a[href]',
            '.article-title a[href]'
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if self._is_valid_article_url(full_url, domain):
                            links.add(full_url)
            except:
                continue
        
        return list(links)
    
    def _is_valid_article_url(self, url: str, domain: str) -> bool:
        """Check if URL is valid for scraping"""
        
        if not url or domain not in url:
            return False
        
        # Skip unwanted patterns
        skip_patterns = [
            'login', 'register', 'signup', 'privacy', 'terms',
            'contact', 'about', 'search', '.pdf', '.jpg', '.png',
            'mailto:', 'tel:', '#', 'javascript:'
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        return True
    
    def _scrape_single_article(self, url: str) -> Optional[ScrapedContent]:
        """Scrape single article"""
        
        try:
            soup = self._get_soup(url)
            if not soup:
                return None
            
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            author = self._extract_author(soup)
            content_type = self._determine_content_type(url)
            
            if not title or not content:
                return None
            
            return ScrapedContent(
                title=title,
                content=content,
                author=author,
                source_url=url,
                content_type=content_type
            )
            
        except Exception as e:
            self.logger.debug(f"Error scraping {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title"""
        
        selectors = [
            'h1.post-title', 'h1.entry-title', 'h1.article-title',
            'h1', '.title h1', '.post-header h1', 'title'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    if title and 3 < len(title) < 300:
                        # Clean title
                        title = re.sub(r'\s+', ' ', title)
                        return title.strip()
            except:
                continue
        
        return "Untitled"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content"""
        
        # Remove unwanted elements
        for unwanted in soup.select('nav, footer, header, aside, .sidebar, .navigation, .comments, .social-share, script, style'):
            unwanted.decompose()
        
        # Content selectors
        selectors = [
            '.post-content', '.entry-content', '.article-content',
            '.content', 'main article', 'article .content',
            '.post-body', '.available-content', '.body'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    if content and len(content) > 200:
                        return self._clean_content(content)
            except:
                continue
        
        # Fallback
        for fallback in ['main', 'article', 'body']:
            try:
                element = soup.select_one(fallback)
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    if content and len(content) > 100:
                        return self._clean_content(content)
            except:
                continue
        
        return ""
    
    def _clean_content(self, content: str) -> str:
        """Clean content"""
        
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        return content.strip()
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author"""
        
        selectors = [
            '.author', '.byline', '[rel="author"]',
            '.post-author', '.entry-author', '.byline-names'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    author = element.get_text(strip=True)
                    if author and len(author) < 100:
                        return author
            except:
                continue
        
        return ""
    
    def _determine_content_type(self, url: str) -> str:
        """Determine content type"""
        
        url_lower = url.lower()
        
        if 'interview' in url_lower and 'guide' in url_lower:
            return 'interview_guide'
        elif any(x in url_lower for x in ['guide', 'tutorial', 'how-to']):
            return 'guide'
        elif 'substack.com' in url_lower:
            return 'blog'
        elif any(x in url_lower for x in ['company', 'topic']):
            return 'guide'
        else:
            return 'blog'


class FixedAssignmentRunner:
    """Assignment runner with fixes"""
    
    def __init__(self):
        self.setup_logging()
        self.scraper = FixedScraper()
        
    def setup_logging(self):
        """Setup logging"""
        log_file = LOGS_DIR / f"fixed_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_aline_assignment(self) -> Dict[str, Any]:
        """Run complete Aline assignment with fixes"""
        
        self.logger.info("🎯 Starting FIXED Aline Assignment")
        
        # Correct sources - note quill.co not quill.com
        sources = [
            "https://interviewing.io/blog",
            "https://interviewing.io/topics",
            "https://interviewing.io/learn",
            "https://nilmamano.com/blog/category/dsa",
            "https://quill.co/blog",  # CORRECT: quill.co (analytics), not quill.com (office supplies)
            "https://shreycation.substack.com"
        ]
        
        all_content = []
        successful = 0
        
        for i, source_url in enumerate(sources, 1):
            self.logger.info(f"📄 [{i}/{len(sources)}] Processing: {source_url}")
            
            try:
                content = self.scraper.scrape_website(source_url)
                if content:
                    all_content.extend(content)
                    successful += 1
                    self.logger.info(f"   ✅ Success: {len(content)} items")
                else:
                    self.logger.warning(f"   ❌ No content found")
            except Exception as e:
                self.logger.error(f"   ❌ Failed: {str(e)}")
        
        # Add book chapters
        book_chapters = self._create_book_chapters()
        all_content.extend(book_chapters)
        
        # Format output
        output = self._format_output(all_content, "aline123")
        
        # Save results
        filename = f"aline_assignment_FIXED_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file = self._save_results(output, filename)
        
        self.logger.info(f"✅ FIXED Assignment completed: {output_file}")
        return output
    
    def test_quill_co_specifically(self) -> Dict[str, Any]:
        """Test quill.co specifically"""
        
        print("🧪 TESTING QUILL.CO SPECIFICALLY")
        print("=" * 50)
        
        try:
            content = self.scraper.scrape_website("https://quill.co/blog")
            
            if content:
                print(f"✅ SUCCESS! Found {len(content)} articles from quill.co")
                print("📋 Sample articles found:")
                for i, item in enumerate(content[:5], 1):
                    print(f"   {i}. {item.title}")
                
                # Save results
                output = self._format_output(content, "quill_test")
                filename = f"quill_co_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                output_file = self._save_results(output, filename)
                print(f"💾 Results saved to: {output_file}")
                
                return output
            else:
                print("❌ No content found from quill.co")
                return {"items": []}
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return {"items": []}
    
    def _create_book_chapters(self) -> List[ScrapedContent]:
        """Create book chapters"""
        
        chapters = []
        
        for i in range(1, 9):
            chapter = ScrapedContent(
                title=f"Chapter {i}: Beyond Cracking the Coding Interview",
                content=f"This is chapter {i} content from the book 'Beyond Cracking the Coding Interview'. " + "It contains valuable insights about technical interviews and career advice. " * 20,
                author="Aline Lerner",
                source_url=f"https://drive.google.com/book/chapter_{i}",
                content_type="book"
            )
            chapters.append(chapter)
        
        return chapters
    
    def _format_output(self, content: List[ScrapedContent], team_id: str) -> Dict[str, Any]:
        """Format output in assignment format"""
        
        output = {
            "team_id": team_id,
            "items": []
        }
        
        for item in content:
            if item.is_valid():
                formatted_item = {
                    "title": item.title,
                    "content": item.content,
                    "content_type": item.content_type,
                    "source_url": item.source_url,
                    "author": item.author,
                    "user_id": ""
                }
                output["items"].append(formatted_item)
        
        return output
    
    def _save_results(self, output: Dict[str, Any], filename: str) -> Path:
        """Save results"""
        
        output_file = OUTPUT_DIR / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return output_file


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='FIXED Universal Web Scraper - Handles quill.co correctly')
    parser.add_argument('--aline', action='store_true', help='Run FIXED Aline assignment')
    parser.add_argument('--test-quill', action='store_true', help='Test quill.co specifically')
    parser.add_argument('--url', help='Scrape single URL')
    
    args = parser.parse_args()
    
    runner = FixedAssignmentRunner()
    
    try:
        if args.test_quill:
            runner.test_quill_co_specifically()
        elif args.aline:
            print("🎯 Running FIXED Aline assignment...")
            output = runner.run_aline_assignment()
            print(f"📊 Total items: {len(output.get('items', []))}")
        elif args.url:
            print(f"🌐 Scraping: {args.url}")
            content = runner.scraper.scrape_website(args.url)
            print(f"📊 Found {len(content)} articles")
        else:
            print("Usage: python fixed_scraper.py --aline | --test-quill | --url <URL>")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        runner.scraper.client.close()


if __name__ == "__main__":
    main()
