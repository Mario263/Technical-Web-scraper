# src/processors/content_processor.py - Content cleaning and processing

import re
import logging
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag, NavigableString
from urllib.parse import urljoin
import html2text

logger = logging.getLogger(__name__)

class ContentCleaner:
    """Clean and process HTML content for better extraction"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.remove_elements = config.get("remove_elements", [
            "nav", "footer", "header", ".sidebar", ".advertisement", 
            ".social-share", ".comments", ".related-posts", ".popup",
            "script", "style", "noscript", ".cookie-notice"
        ])
        
    def clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Clean HTML by removing unwanted elements and attributes"""
        
        # Remove unwanted elements
        self._remove_unwanted_elements(soup)
        
        # Clean attributes
        self._clean_attributes(soup)
        
        # Fix malformed HTML
        self._fix_malformed_html(soup)
        
        # Remove empty elements
        self._remove_empty_elements(soup)
        
        return soup
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """Remove navigation, ads, and other unwanted elements"""
        
        for selector in self.remove_elements:
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    # CSS selector
                    elements = soup.select(selector)
                else:
                    # Tag name
                    elements = soup.find_all(selector)
                
                for element in elements:
                    logger.debug(f"Removing element: {selector}")
                    element.decompose()
                    
            except Exception as e:
                logger.debug(f"Error removing {selector}: {str(e)}")
        
        # Remove elements with specific classes/IDs that indicate non-content
        unwanted_patterns = [
            'nav', 'navigation', 'menu', 'sidebar', 'footer', 'header',
            'ad', 'ads', 'advertisement', 'banner', 'popup', 'modal',
            'social', 'share', 'comment', 'related', 'recommend',
            'cookie', 'consent', 'gdpr', 'newsletter', 'subscribe'
        ]
        
        for element in soup.find_all(True):
            if element.get('class') or element.get('id'):
                classes = ' '.join(element.get('class', [])).lower()
                element_id = (element.get('id') or '').lower()
                
                for pattern in unwanted_patterns:
                    if pattern in classes or pattern in element_id:
                        logger.debug(f"Removing element with pattern '{pattern}': {element.name}")
                        element.decompose()
                        break
    
    def _clean_attributes(self, soup: BeautifulSoup):
        """Clean HTML attributes, keeping only essential ones"""
        
        # Attributes to keep for different elements
        keep_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title'],
            'code': ['class'],
            'pre': ['class'],
            'blockquote': ['cite'],
            'table': [],
            'th': [],
            'td': [],
            'tr': [],
            'ul': [],
            'ol': [],
            'li': []
        }
        
        for element in soup.find_all(True):
            if element.name in keep_attributes:
                # Keep only allowed attributes
                allowed_attrs = keep_attributes[element.name]
                attrs_to_remove = [attr for attr in element.attrs if attr not in allowed_attrs]
                
                for attr in attrs_to_remove:
                    del element[attr]
            else:
                # For other elements, remove all attributes except href for links
                if element.name == 'a' and 'href' in element.attrs:
                    href = element['href']
                    element.attrs.clear()
                    element['href'] = href
                else:
                    element.attrs.clear()
    
    def _fix_malformed_html(self, soup: BeautifulSoup):
        """Fix common HTML issues"""
        
        # Fix nested paragraphs
        for p in soup.find_all('p'):
            nested_p = p.find('p')
            if nested_p:
                # Move nested paragraph content up
                nested_p.unwrap()
        
        # Fix div tags that should be paragraphs
        for div in soup.find_all('div'):
            if not div.find(['div', 'p', 'ul', 'ol', 'blockquote', 'pre']):
                div.name = 'p'
        
        # Remove excessive line breaks
        for br in soup.find_all('br'):
            # Remove multiple consecutive <br> tags
            next_sibling = br.next_sibling
            if next_sibling and next_sibling.name == 'br':
                br.decompose()
    
    def _remove_empty_elements(self, soup: BeautifulSoup):
        """Remove elements that are empty or contain only whitespace"""
        
        # Elements that can be empty (self-closing)
        self_closing = {'br', 'hr', 'img', 'input', 'meta', 'link'}
        
        # Remove empty elements (but keep self-closing ones)
        for element in soup.find_all(True):
            if element.name not in self_closing:
                if not element.get_text(strip=True) and not element.find(['img', 'hr', 'br']):
                    element.decompose()


class MarkdownConverter:
    """Convert cleaned HTML to markdown format"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.h2t = html2text.HTML2Text()
        self._configure_html2text()
    
    def _configure_html2text(self):
        """Configure html2text converter"""
        self.h2t.ignore_links = False
        self.h2t.ignore_images = not self.config.get("preserve_images", False)
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # No line wrapping
        self.h2t.unicode_snob = True
        self.h2t.escape_snob = True
        
        # Preserve code blocks
        if self.config.get("preserve_code_blocks", True):
            self.h2t.ignore_code = False
        
        # Preserve links
        if self.config.get("preserve_links", True):
            self.h2t.ignore_links = False
    
    def convert_to_markdown(self, html_content: str, base_url: str = "") -> str:
        """Convert HTML content to clean markdown"""
        
        if not html_content:
            return ""
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Clean the HTML first
        cleaner = ContentCleaner(self.config)
        cleaned_soup = cleaner.clean_html(soup)
        
        # Convert to markdown
        markdown_content = self.h2t.handle(str(cleaned_soup))
        
        # Post-process markdown
        markdown_content = self._post_process_markdown(markdown_content)
        
        # Fix relative URLs if base_url provided
        if base_url:
            markdown_content = self._fix_relative_urls(markdown_content, base_url)
        
        return markdown_content.strip()
    
    def _post_process_markdown(self, markdown: str) -> str:
        """Clean up and improve markdown formatting"""
        
        # Remove excessive whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Max 2 consecutive newlines
        markdown = re.sub(r'[ \t]+\n', '\n', markdown)  # Remove trailing spaces
        markdown = re.sub(r'\n[ \t]+', '\n', markdown)  # Remove leading spaces on new lines
        
        # Fix markdown list formatting
        markdown = re.sub(r'\n-\s*\n', '\n- ', markdown)
        markdown = re.sub(r'\n\*\s*\n', '\n* ', markdown)
        
        # Fix code block formatting
        markdown = re.sub(r'```\s*\n\s*```', '', markdown)  # Remove empty code blocks
        
        # Fix heading spacing
        markdown = re.sub(r'\n(#{1,6})', r'\n\n\1', markdown)
        markdown = re.sub(r'(#{1,6}.*)\n([^\n#])', r'\1\n\n\2', markdown)
        
        # Fix blockquote formatting
        markdown = re.sub(r'\n>\s*\n', '\n> ', markdown)
        
        # Remove markdown artifacts
        markdown = re.sub(r'\\_', '_', markdown)  # Fix escaped underscores
        markdown = re.sub(r'\\#', '#', markdown)   # Fix escaped hashes
        
        return markdown
    
    def _fix_relative_urls(self, markdown: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs in markdown"""
        
        def replace_url(match):
            url = match.group(2)
            if url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                return match.group(0)  # Already absolute
            else:
                absolute_url = urljoin(base_url, url)
                return f"{match.group(1)}{absolute_url}{match.group(3)}"
        
        # Fix markdown links: [text](url)
        markdown = re.sub(r'(\[.*?\]\()([^)]+)(\))', replace_url, markdown)
        
        # Fix markdown images: ![alt](url)
        markdown = re.sub(r'(!\[.*?\]\()([^)]+)(\))', replace_url, markdown)
        
        return markdown


class ContentQualityScorer:
    """Score content quality based on various metrics"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_length = config.get("min_content_length", 100)
        self.max_length = config.get("max_content_length", 50000)
    
    def score_content(self, content: str, metadata: Dict) -> float:
        """Calculate quality score for content (0.0 to 1.0)"""
        
        if not content:
            return 0.0
        
        scores = []
        
        # Length score
        scores.append(self._score_length(content))
        
        # Structure score
        scores.append(self._score_structure(content))
        
        # Technical content score
        scores.append(self._score_technical_content(content))
        
        # Readability score
        scores.append(self._score_readability(content))
        
        # Completeness score
        scores.append(self._score_completeness(content, metadata))
        
        # Calculate weighted average
        weights = [0.2, 0.2, 0.3, 0.15, 0.15]  # Emphasize technical content
        final_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return min(1.0, max(0.0, final_score))
    
    def _score_length(self, content: str) -> float:
        """Score based on content length"""
        length = len(content)
        
        if length < self.min_length:
            return 0.0
        elif length > self.max_length:
            return 0.5  # Too long might be problematic
        else:
            # Optimal range: 500-5000 characters
            if 500 <= length <= 5000:
                return 1.0
            elif length < 500:
                return length / 500
            else:
                return max(0.5, 1.0 - (length - 5000) / 10000)
    
    def _score_structure(self, content: str) -> float:
        """Score based on document structure"""
        score = 0.0
        
        # Has headings
        if re.search(r'^#{1,6}\s+.+', content, re.MULTILINE):
            score += 0.3
        
        # Has lists
        if re.search(r'^\s*[-*+]\s+.+', content, re.MULTILINE):
            score += 0.2
        
        # Has numbered lists
        if re.search(r'^\s*\d+\.\s+.+', content, re.MULTILINE):
            score += 0.2
        
        # Has code blocks
        if '```' in content or '`' in content:
            score += 0.2
        
        # Has paragraphs (multiple line breaks)
        if content.count('\n\n') >= 2:
            score += 0.1
        
        return min(1.0, score)
    
    def _score_technical_content(self, content: str) -> float:
        """Score based on technical content indicators"""
        score = 0.0
        content_lower = content.lower()
        
        # Technical keywords
        tech_keywords = [
            'algorithm', 'data structure', 'programming', 'coding', 'software',
            'interview', 'technical', 'engineering', 'development', 'code',
            'function', 'class', 'method', 'variable', 'api', 'database',
            'system design', 'architecture', 'performance', 'optimization'
        ]
        
        keyword_count = sum(1 for keyword in tech_keywords if keyword in content_lower)
        score += min(0.5, keyword_count * 0.05)
        
        # Code snippets
        if '```' in content:
            score += 0.3
        elif '`' in content:
            score += 0.1
        
        # Technical patterns
        if re.search(r'\b(O\([^)]+\))', content):  # Big O notation
            score += 0.2
        
        return min(1.0, score)
    
    def _score_readability(self, content: str) -> float:
        """Score based on readability metrics"""
        if not content:
            return 0.0
        
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        if not words or not sentences:
            return 0.0
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        word_score = 1.0 if 4 <= avg_word_length <= 6 else 0.5
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        sentence_score = 1.0 if 10 <= avg_sentence_length <= 25 else 0.5
        
        return (word_score + sentence_score) / 2
    
    def _score_completeness(self, content: str, metadata: Dict) -> float:
        """Score based on content completeness"""
        score = 0.0
        
        # Has title
        if metadata.get('title'):
            score += 0.3
        
        # Has author
        if metadata.get('author'):
            score += 0.2
        
        # Has date
        if metadata.get('date'):
            score += 0.2
        
        # Content doesn't appear truncated
        if not content.endswith(('...', '[...]', 'Read more')):
            score += 0.3
        
        return score


# Factory functions
def create_content_cleaner(config: Dict) -> ContentCleaner:
    """Factory function to create content cleaner"""
    return ContentCleaner(config)

def create_markdown_converter(config: Dict) -> MarkdownConverter:
    """Factory function to create markdown converter"""
    return MarkdownConverter(config)

def create_quality_scorer(config: Dict) -> ContentQualityScorer:
    """Factory function to create quality scorer"""
    return ContentQualityScorer(config)