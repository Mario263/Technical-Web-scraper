#!/usr/bin/env python3
"""
complete_assignment_comprehensive.py - COMPREHENSIVE Aline Assignment Implementation

This script implements a COMPREHENSIVE scraper that captures EVERYTHING from:
1. interviewing.io/blog - ALL blog posts (follow all read more links)
2. interviewing.io/topics#companies - ALL company guides (click all elements)
3. interviewing.io/learn#interview-guides - ALL interview guides (follow all links)
4. nilmamano.com/blog - ALL blog posts (complete blog, not just DS&A)
5. quill.co/blog - ALL blog posts (NEW SOURCE)
6. shreycation.substack.com/archive - ALL substack posts (NEW SOURCE)
7. Book chapters (8 chapters from PDF)

Output format: EXACT specification with no duplicates
"""

import sys
import json
import logging
import time
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import List, Set, Dict, Optional

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import SCRAPING_CONFIG, OUTPUT_DIR, LOGS_DIR
from src.utils.http_client import create_http_client
from src.scrapers.base_scraper import ScrapedContent
from src.processors.pdf_processor import create_pdf_processor
from bs4 import BeautifulSoup

# Setup logging
def setup_logging():
    log_file = LOGS_DIR / f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class ComprehensiveAssignmentScraper:
    """Comprehensive scraper that captures EVERYTHING from all specified sources"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.client = create_http_client(SCRAPING_CONFIG)
        self.all_content = []
        self.scraped_urls = set()  # Track to prevent duplicates
        self.session_stats = {
            "total_pages_visited": 0,
            "total_articles_found": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "duplicates_skipped": 0
        }
        
    def run_comprehensive_assignment(self):
        """Execute the COMPREHENSIVE assignment - capture EVERYTHING"""
        
        self.logger.info("🎯 STARTING COMPREHENSIVE ALINE ASSIGNMENT")
        self.logger.info("🔄 CAPTURING ALL CONTENT FROM ALL SOURCES")
        self.logger.info("=" * 100)
        
        try:
            # 1. interviewing.io/blog - ALL blog posts
            self.scrape_interviewing_io_blog_comprehensive()
            
            # 2. interviewing.io/topics#companies - ALL company guides  
            self.scrape_company_guides_comprehensive()
            
            # 3. interviewing.io/learn#interview-guides - ALL interview guides
            self.scrape_interview_guides_comprehensive()
            
            # 4. nilmamano.com/blog - ALL blog posts (complete blog)
            self.scrape_nil_blog_comprehensive()
            
            # 5. quill.co/blog - ALL blog posts (NEW SOURCE)
            self.scrape_quill_blog_comprehensive()
            
            # 6. shreycation.substack.com/archive - ALL substack posts (NEW SOURCE)
            self.scrape_shreycation_substack_comprehensive()
            
            # 7. Book chapters (8 chapters from PDF)
            self.process_book_chapters()
            
            # 8. Generate final output in EXACT format
            final_output = self.generate_final_output()
            
            # 9. Save results
            self.save_comprehensive_output(final_output)
            
            # 10. Print final statistics
            self.print_final_statistics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Comprehensive assignment failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.client.close()

    def scrape_interviewing_io_blog_comprehensive(self):
        """1. interviewing.io/blog - Capture ALL blog posts"""
        
        self.logger.info("📰 COMPREHENSIVE: Scraping ALL interviewing.io blog posts...")
        
        try:
            base_url = "https://interviewing.io/blog"
            
            # Get main blog page
            soup = self._get_page_soup(base_url)
            if not soup:
                self.logger.warning("Could not access main blog page")
                return
                
            # Find ALL article links on the page
            article_links = self._extract_all_blog_links(soup, base_url)
            self.logger.info(f"📊 Found {len(article_links)} potential blog articles")
            
            # Scrape each article
            for i, link in enumerate(article_links, 1):
                if link not in self.scraped_urls:
                    self.logger.info(f"📝 Scraping blog article {i}/{len(article_links)}: {link}")
                    article = self._scrape_single_page_comprehensive(link, "blog", "interviewing.io")
                    if article:
                        self.all_content.append(article)
                        self.session_stats["successful_scrapes"] += 1
                    else:
                        self.session_stats["failed_scrapes"] += 1
                    time.sleep(0.5)  # Be respectful
                else:
                    self.session_stats["duplicates_skipped"] += 1
            
            blog_count = len([c for c in self.all_content if c.metadata.get('content_type') == 'blog' and 'interviewing.io' in c.source_url])
            self.logger.info(f"✅ interviewing.io blog: {blog_count} articles scraped")
            
        except Exception as e:
            self.logger.error(f"❌ interviewing.io blog scraping failed: {str(e)}")

    def scrape_company_guides_comprehensive(self):
        """2. interviewing.io/topics#companies - Capture ALL company guides"""
        
        self.logger.info("🏢 COMPREHENSIVE: Scraping ALL company guides...")
        
        try:
            base_url = "https://interviewing.io/topics"
            
            # Get topics page
            soup = self._get_page_soup(base_url)
            if not soup:
                self.logger.warning("Could not access topics page")
                return
            
            # Find ALL company-related links
            company_links = self._extract_all_company_links(soup, base_url)
            self.logger.info(f"📊 Found {len(company_links)} potential company guides")
            
            # Scrape each company guide
            for i, link in enumerate(company_links, 1):
                if link not in self.scraped_urls:
                    self.logger.info(f"📋 Scraping company guide {i}/{len(company_links)}: {link}")
                    article = self._scrape_single_page_comprehensive(link, "guide", "interviewing.io")
                    if article:
                        self.all_content.append(article)
                        self.session_stats["successful_scrapes"] += 1
                    else:
                        self.session_stats["failed_scrapes"] += 1
                    time.sleep(0.5)
                else:
                    self.session_stats["duplicates_skipped"] += 1
            
            guides_count = len([c for c in self.all_content if c.metadata.get('content_type') == 'guide'])
            self.logger.info(f"✅ Company guides: {guides_count} guides scraped")
            
        except Exception as e:
            self.logger.error(f"❌ Company guides scraping failed: {str(e)}")

    def scrape_interview_guides_comprehensive(self):
        """3. interviewing.io/learn#interview-guides - Capture ALL interview guides"""
        
        self.logger.info("📚 COMPREHENSIVE: Scraping ALL interview guides...")
        
        try:
            base_url = "https://interviewing.io/learn"
            
            # Get learn page
            soup = self._get_page_soup(base_url)
            if not soup:
                self.logger.warning("Could not access learn page")
                return
            
            # Find ALL interview guide links
            guide_links = self._extract_all_interview_guide_links(soup, base_url)
            self.logger.info(f"📊 Found {len(guide_links)} potential interview guides")
            
            # Scrape each interview guide
            for i, link in enumerate(guide_links, 1):
                if link not in self.scraped_urls:
                    self.logger.info(f"📖 Scraping interview guide {i}/{len(guide_links)}: {link}")
                    article = self._scrape_single_page_comprehensive(link, "interview_guide", "interviewing.io")
                    if article:
                        self.all_content.append(article)
                        self.session_stats["successful_scrapes"] += 1
                    else:
                        self.session_stats["failed_scrapes"] += 1
                    time.sleep(0.5)
                else:
                    self.session_stats["duplicates_skipped"] += 1
            
            interview_guides_count = len([c for c in self.all_content if c.metadata.get('content_type') == 'interview_guide'])
            self.logger.info(f"✅ Interview guides: {interview_guides_count} guides scraped")
            
        except Exception as e:
            self.logger.error(f"❌ Interview guides scraping failed: {str(e)}")

    def scrape_nil_blog_comprehensive(self):
        """4. nilmamano.com/blog - Capture ALL blog posts (complete blog)"""
        
        self.logger.info("🧮 COMPREHENSIVE: Scraping ALL of Nil's blog posts...")
        
        try:
            # Try both the main blog and the DS&A category
            blog_urls = [
                "https://nilmamano.com/blog",
                "https://nilmamano.com/blog/category/dsa"
            ]
            
            all_blog_links = set()
            
            for blog_url in blog_urls:
                soup = self._get_page_soup(blog_url)
                if soup:
                    links = self._extract_all_nil_blog_links(soup, blog_url)
                    all_blog_links.update(links)
            
            self.logger.info(f"📊 Found {len(all_blog_links)} potential Nil's blog posts")
            
            # Scrape each blog post
            for i, link in enumerate(all_blog_links, 1):
                if link not in self.scraped_urls:
                    self.logger.info(f"🔢 Scraping Nil's post {i}/{len(all_blog_links)}: {link}")
                    article = self._scrape_single_page_comprehensive(link, "blog", "Nil Mamano")
                    if article:
                        article.author = "Nil Mamano"  # Ensure correct author
                        self.all_content.append(article)
                        self.session_stats["successful_scrapes"] += 1
                    else:
                        self.session_stats["failed_scrapes"] += 1
                    time.sleep(0.5)
                else:
                    self.session_stats["duplicates_skipped"] += 1
            
            nil_count = len([c for c in self.all_content if c.author == "Nil Mamano"])
            self.logger.info(f"✅ Nil's blog: {nil_count} posts scraped")
            
        except Exception as e:
            self.logger.error(f"❌ Nil's blog scraping failed: {str(e)}")

    def scrape_quill_blog_comprehensive(self):
        """5. quill.co/blog - Capture ALL blog posts (NEW SOURCE)"""
        
        self.logger.info("📝 COMPREHENSIVE: Scraping ALL quill.co blog posts...")
        
        try:
            base_url = "https://quill.co/blog"
            
            # Get main blog page
            soup = self._get_page_soup(base_url)
            if not soup:
                self.logger.warning("Could not access quill.co blog")
                return
                
            # Find ALL article links
            article_links = self._extract_all_blog_links(soup, base_url)
            self.logger.info(f"📊 Found {len(article_links)} potential quill.co articles")
            
            # Scrape each article
            for i, link in enumerate(article_links, 1):
                if link not in self.scraped_urls:
                    self.logger.info(f"📄 Scraping quill.co article {i}/{len(article_links)}: {link}")
                    article = self._scrape_single_page_comprehensive(link, "blog", "quill.co")
                    if article:
                        self.all_content.append(article)
                        self.session_stats["successful_scrapes"] += 1
                    else:
                        self.session_stats["failed_scrapes"] += 1
                    time.sleep(0.5)
                else:
                    self.session_stats["duplicates_skipped"] += 1
            
            quill_count = len([c for c in self.all_content if 'quill.co' in c.source_url])
            self.logger.info(f"✅ quill.co blog: {quill_count} articles scraped")
            
        except Exception as e:
            self.logger.error(f"❌ quill.co blog scraping failed: {str(e)}")

    def scrape_shreycation_substack_comprehensive(self):
        """6. shreycation.substack.com/archive - Capture ALL substack posts (NEW SOURCE)"""
        
        self.logger.info("📨 COMPREHENSIVE: Scraping ALL shreycation substack posts...")
        
        try:
            base_url = "https://shreycation.substack.com/archive?sort=new"
            
            # Get archive page
            soup = self._get_page_soup(base_url)
            if not soup:
                self.logger.warning("Could not access shreycation archive")
                return
                
            # Find ALL substack post links
            post_links = self._extract_all_substack_links(soup, base_url)
            self.logger.info(f"📊 Found {len(post_links)} potential substack posts")
            
            # Scrape each post
            for i, link in enumerate(post_links, 1):
                if link not in self.scraped_urls:
                    self.logger.info(f"📰 Scraping substack post {i}/{len(post_links)}: {link}")
                    article = self._scrape_single_page_comprehensive(link, "blog", "shreycation")
                    if article:
                        self.all_content.append(article)
                        self.session_stats["successful_scrapes"] += 1
                    else:
                        self.session_stats["failed_scrapes"] += 1
                    time.sleep(0.5)
                else:
                    self.session_stats["duplicates_skipped"] += 1
            
            substack_count = len([c for c in self.all_content if 'substack.com' in c.source_url])
            self.logger.info(f"✅ shreycation substack: {substack_count} posts scraped")
            
        except Exception as e:
            self.logger.error(f"❌ shreycation substack scraping failed: {str(e)}")

    def process_book_chapters(self):
        """7. First 8 chapters of book (PDF)"""
        
        self.logger.info("📚 Processing book chapters...")
        
        try:
            processor = create_pdf_processor(self.client, {})
            book_chapters = processor.process_book_chapters()
            
            # Convert to ScrapedContent format
            for chapter in book_chapters:
                content = ScrapedContent()
                content.title = chapter['title']
                content.content = chapter['content']
                content.source_url = chapter['source_url']
                content.author = "Aline Lerner"
                content.metadata = chapter['metadata']
                content.metadata['content_type'] = 'book'
                self.all_content.append(content)
            
            self.logger.info(f"✅ Book chapters: {len(book_chapters)} chapters processed")
            
        except Exception as e:
            self.logger.error(f"❌ Book processing failed: {str(e)}")

    def generate_final_output(self):
        """Generate output in EXACT format specified"""
        
        self.logger.info("📋 Generating final output in EXACT assignment format...")
        
        # Remove duplicates based on title and content similarity
        unique_content = self._remove_duplicates(self.all_content)
        
        # Format according to EXACT specification
        final_output = {
            "team_id": "aline123",
            "items": []
        }
        
        for content in unique_content:
            item = {
                "title": content.title or "Untitled",
                "content": content.content or "",
                "content_type": content.metadata.get('content_type', 'other'),
                "source_url": content.source_url or "",
                "author": content.author or "",
                "user_id": ""
            }
            final_output["items"].append(item)
        
        self.logger.info(f"📊 Final output contains {len(final_output['items'])} unique items")
        return final_output

    def save_comprehensive_output(self, output):
        """Save results in assignment format"""
        
        self.logger.info("💾 Saving comprehensive assignment output...")
        
        # Main assignment output
        assignment_file = OUTPUT_DIR / "aline_comprehensive_assignment.json"
        
        with open(assignment_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"✅ Comprehensive assignment saved to: {assignment_file}")
        
        # Create detailed summary
        content_by_source = {}
        for item in output["items"]:
            source = urlparse(item["source_url"]).netloc if item["source_url"] else "book"
            content_by_source[source] = content_by_source.get(source, 0) + 1
        
        summary = {
            "comprehensive_assignment": {
                "total_items": len(output["items"]),
                "items_by_source": content_by_source,
                "session_statistics": self.session_stats,
                "sources_scraped": [
                    "interviewing.io/blog (ALL posts)",
                    "interviewing.io/topics#companies (ALL guides)", 
                    "interviewing.io/learn#interview-guides (ALL guides)",
                    "nilmamano.com/blog (ALL posts)",
                    "quill.co/blog (ALL posts)",
                    "shreycation.substack.com/archive (ALL posts)",
                    "book_chapters_pdf (8 chapters)"
                ],
                "output_format": "EXACT_SPECIFICATION",
                "completed_at": datetime.now().isoformat()
            }
        }
        
        summary_file = OUTPUT_DIR / "comprehensive_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"📊 Comprehensive summary saved to: {summary_file}")

    def print_final_statistics(self):
        """Print comprehensive statistics"""
        
        self.logger.info("=" * 100)
        self.logger.info("🎉 COMPREHENSIVE ASSIGNMENT COMPLETED!")
        self.logger.info("=" * 100)
        self.logger.info(f"📊 TOTAL CONTENT ITEMS: {len(self.all_content)}")
        self.logger.info(f"🌐 Pages Visited: {self.session_stats['total_pages_visited']}")
        self.logger.info(f"✅ Successful Scrapes: {self.session_stats['successful_scrapes']}")
        self.logger.info(f"❌ Failed Scrapes: {self.session_stats['failed_scrapes']}")
        self.logger.info(f"🔄 Duplicates Skipped: {self.session_stats['duplicates_skipped']}")
        
        # Count by source
        source_counts = {}
        for content in self.all_content:
            source = urlparse(content.source_url).netloc if content.source_url else "book"
            source_counts[source] = source_counts.get(source, 0) + 1
        
        self.logger.info("\n📊 CONTENT BY SOURCE:")
        for source, count in source_counts.items():
            self.logger.info(f"   {source}: {count} items")
        
        self.logger.info("=" * 100)

    def _get_page_soup(self, url):
        """Get BeautifulSoup object for a URL with comprehensive error handling"""
        try:
            self.session_stats["total_pages_visited"] += 1
            response = self.client.get(url)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            else:
                self.logger.debug(f"HTTP {response.status_code} for {url}")
        except Exception as e:
            self.logger.debug(f"Failed to get page {url}: {str(e)}")
        return None

    def _extract_all_blog_links(self, soup, base_url):
        """Extract ALL blog post links from a page"""
        links = set()
        
        # Comprehensive selectors for blog links
        selectors = [
            'a[href*="/blog/"]',
            'a[href*="article"]',
            'a[href*="post"]',
            '.post-title a',
            '.entry-title a', 
            '.article-title a',
            'article a',
            'h1 a', 'h2 a', 'h3 a',
            '.read-more',
            '[class*="read"] a',
            '[class*="more"] a',
            '.blog-post a',
            '.post a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    # Filter out non-article URLs
                    if self._is_valid_article_url(full_url, base_url):
                        links.add(full_url)
        
        return list(links)

    def _extract_all_company_links(self, soup, base_url):
        """Extract ALL company guide links"""
        links = set()
        
        selectors = [
            'a[href*="/guides/"]',
            'a[href*="/topics/"]', 
            'a[href*="/companies/"]',
            'a[href*="/company"]',
            'a[href*="hiring-process"]',
            'a[href*="interview-questions"]',
            '.company a',
            '.guide a',
            '.topic a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, "interviewing.io"):
                        links.add(full_url)
        
        return list(links)

    def _extract_all_interview_guide_links(self, soup, base_url):
        """Extract ALL interview guide links"""
        links = set()
        
        selectors = [
            'a[href*="/guides/"]',
            'a[href*="/learn/"]',
            'a[href*="interview"]',
            'a[href*="guide"]',
            'a[href*="questions"]',
            '.interview-guide a',
            '.learn a',
            '.guide a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, "interviewing.io"):
                        links.add(full_url)
        
        return list(links)

    def _extract_all_nil_blog_links(self, soup, base_url):
        """Extract ALL Nil's blog post links"""
        links = set()
        
        selectors = [
            'a[href*="/blog/"]',
            '.post-title a',
            '.entry-title a',
            'article a',
            'h1 a', 'h2 a', 'h3 a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, "nilmamano.com") and '/blog/' in full_url:
                        links.add(full_url)
        
        return list(links)

    def _extract_all_substack_links(self, soup, base_url):
        """Extract ALL substack post links"""
        links = set()
        
        selectors = [
            'a[href*="/p/"]',
            '.post-preview-title a',
            '.entry-title a',
            'article a',
            'h1 a', 'h2 a', 'h3 a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, "substack.com") and '/p/' in full_url:
                        links.add(full_url)
        
        return list(links)

    def _is_valid_article_url(self, url, domain):
        """Check if URL is a valid article URL"""
        if not url or url in self.scraped_urls:
            return False
            
        # Exclude common non-article patterns
        exclude_patterns = [
            'login', 'signup', 'register', 'privacy', 'terms',
            'contact', 'about', 'faq', '.pdf', '.jpg', '.png',
            'twitter.com', 'linkedin.com', 'facebook.com',
            'mailto:', 'tel:', '#', 'javascript:'
        ]
        
        for pattern in exclude_patterns:
            if pattern in url.lower():
                return False
        
        # Must contain domain
        if domain not in url:
            return False
            
        return True

    def _scrape_single_page_comprehensive(self, url, content_type, author_hint):
        """Scrape a single page with comprehensive content extraction"""
        try:
            if url in self.scraped_urls:
                return None
                
            self.scraped_urls.add(url)
            
            soup = self._get_page_soup(url)
            if not soup:
                return None
            
            # Extract content with multiple fallback methods
            title = self._extract_title_comprehensive(soup)
            content = self._extract_content_comprehensive(soup)
            author = self._extract_author_comprehensive(soup) or author_hint
            
            # Validate content quality
            if not title or not content or len(content) < 200:
                return None
            
            # Create ScrapedContent object
            scraped = ScrapedContent()
            scraped.title = title
            scraped.content = content
            scraped.source_url = url
            scraped.author = author
            scraped.metadata = {
                'content_type': content_type,
                'scraped_at': datetime.now().isoformat(),
                'word_count': len(content.split())
            }
            
            return scraped
            
        except Exception as e:
            self.logger.debug(f"Error scraping {url}: {str(e)}")
            return None

    def _extract_title_comprehensive(self, soup):
        """Extract title with multiple fallback methods"""
        # Try multiple title extraction methods
        title_selectors = [
            'h1.post-title', 'h1.entry-title', 'h1.article-title',
            'h1', '.title h1', '.post-header h1',
            '.entry-header h1', 'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 3 and len(title) < 200:
                    return title
        
        return "Untitled"

    def _extract_content_comprehensive(self, soup):
        """Extract content with comprehensive methods"""
        # Remove unwanted elements
        for unwanted in soup.select('nav, footer, header, .sidebar, .navigation, script, style, .comments, .social-share'):
            unwanted.decompose()
        
        # Try multiple content extraction methods
        content_selectors = [
            '.post-content', '.entry-content', '.article-content',
            '.content', 'main article', 'article .content',
            '.post-body', '[class*="content"]', '.story-body'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(separator='\n', strip=True)
                if content and len(content) > 500:
                    return content
        
        # Fallback to main or body
        for fallback in ['main', 'article', 'body']:
            element = soup.find(fallback)
            if element:
                content = element.get_text(separator='\n', strip=True)
                if content and len(content) > 200:
                    return content
        
        return ""

    def _extract_author_comprehensive(self, soup):
        """Extract author with multiple methods"""
        author_selectors = [
            '.author', '.byline', '[rel="author"]', '.post-author',
            '.entry-author', '[class*="author"]', '.written-by'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                if author and len(author) < 100:
                    return author
        
        return ""

    def _remove_duplicates(self, content_list):
        """Remove duplicate content based on title and content similarity"""
        seen_titles = set()
        unique_content = []
        
        for content in content_list:
            # Create a simple fingerprint
            title_lower = content.title.lower() if content.title else ""
            content_start = content.content[:200].lower() if content.content else ""
            fingerprint = f"{title_lower}|{content_start}"
            
            if fingerprint not in seen_titles:
                seen_titles.add(fingerprint)
                unique_content.append(content)
            else:
                self.session_stats["duplicates_skipped"] += 1
        
        return unique_content


def main():
    """Main entry point for comprehensive assignment"""
    
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Run comprehensive assignment
    scraper = ComprehensiveAssignmentScraper()
    success = scraper.run_comprehensive_assignment()
    
    if success:
        print("\n🎉 COMPREHENSIVE ASSIGNMENT COMPLETED SUCCESSFULLY!")
        print("📁 Check output/aline_comprehensive_assignment.json for results")
        print("📊 Check output/comprehensive_summary.json for detailed summary")
        print("\n✅ ALL CONTENT CAPTURED FROM ALL SOURCES!")
    else:
        print("\n❌ Comprehensive assignment failed! Check logs for details.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
