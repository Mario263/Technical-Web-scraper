# src/formatters/json_formatter.py - JSON output formatter

import json
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import jsonschema

from ..scrapers.base_scraper import ScrapedContent

logger = logging.getLogger(__name__)

class JSONFormatter:
    """Format scraped content into standardized JSON output"""
    
    def __init__(self, config: Dict, schema_path: Path = None):
        self.config = config
        self.team_id = config.get("team_id", "aline123")  # Default to assignment requirement
        self.schema = None
        
        if schema_path and schema_path.exists():
            try:
                with open(schema_path, 'r') as f:
                    self.schema = json.load(f)
                logger.info("JSON schema loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load schema: {str(e)}")
    
    def format_content_item(self, content: ScrapedContent) -> Dict[str, Any]:
        """Format a single scraped content item to match assignment specification"""
        
        if not content or not content.is_valid():
            logger.warning("Invalid content provided to formatter")
            return None
        
        # Determine content type
        content_type = self._determine_content_type(content)
        
        # Build the item according to specification
        item = {
            "title": content.title.strip() if content.title else "",
            "content": content.content.strip() if content.content else "",
            "content_type": content_type,
            "source_url": content.source_url if content.source_url else "",
            "author": content.author.strip() if content.author else "",
            "user_id": "aline_lerner_001"  # As per assignment context
        }
        
        return item
    
    def _determine_content_type(self, content: ScrapedContent) -> str:
        """Determine content type based on content and metadata"""
        
        # Check if explicitly set in source config
        if hasattr(content, 'metadata') and content.metadata:
            explicit_type = content.metadata.get('content_type')
            if explicit_type:
                return explicit_type
        
        # Default to blog for most content
        return "blog"
    
    def format_output(self, content_items: List[ScrapedContent], 
                     additional_metadata: Dict = None) -> Dict[str, Any]:
        """Format complete output with all content items - matches assignment specification"""
        
        if not content_items:
            logger.warning("No content items provided")
            return {
                "team_id": self.team_id,
                "items": []
            }
        
        formatted_items = []
        
        for content in content_items:
            formatted_item = self.format_content_item(content)
            if formatted_item:
                formatted_items.append(formatted_item)
        
        # Output matches exact assignment specification
        output = {
            "team_id": self.team_id,
            "items": formatted_items
        }
        
        logger.info(f"Formatted {len(formatted_items)} content items")
        return output
    
    def format_complete_output(self, content_items: List[ScrapedContent], 
                              additional_metadata: Dict = None) -> Dict[str, Any]:
        """Format complete output with all content items (alias for format_output)"""
        return self.format_output(content_items, additional_metadata)
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate output against JSON schema"""
        
        if not self.schema:
            logger.warning("No schema available for validation")
            return True  # Assume valid if no schema
        
        try:
            jsonschema.validate(output, self.schema)
            logger.info("✅ Output validated successfully against schema")
            return True
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"❌ Schema validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}")
            return False
    
    def save_output(self, output: Dict[str, Any], output_path: Path) -> bool:
        """Save formatted output to file"""
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Output saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save output: {str(e)}")
            return False


class BatchProcessor:
    """Process multiple sources and combine outputs"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.formatter = JSONFormatter(config)
        self.processed_sources = []
        self.total_items = 0
        self.failed_sources = []
    
    def process_source(self, scraper, source_name: str, max_articles: int = 50) -> List[ScrapedContent]:
        """Process a single content source"""
        
        logger.info(f"Processing source: {source_name}")
        
        try:
            articles = scraper.scrape_source(max_articles=max_articles)
            
            if articles:
                self.processed_sources.append({
                    "source_name": source_name,
                    "articles_count": len(articles),
                    "success": True
                })
                self.total_items += len(articles)
                logger.info(f"✅ {source_name}: {len(articles)} articles processed")
            else:
                self.failed_sources.append(source_name)
                logger.warning(f"⚠️ {source_name}: No articles found")
            
            return articles
            
        except Exception as e:
            logger.error(f"❌ {source_name}: Processing failed - {str(e)}")
            self.failed_sources.append(source_name)
            return []
    
    def combine_and_format(self, all_content: List[List[ScrapedContent]], 
                          output_path: Path) -> bool:
        """Combine all content and create final output"""
        
        # Flatten all content
        combined_content = []
        for content_list in all_content:
            combined_content.extend(content_list)
        
        if not combined_content:
            logger.error("No content to format")
            return False
        
        # Remove duplicates based on content hash
        unique_content = self._deduplicate_content(combined_content)
        
        # Generate processing metadata
        processing_metadata = {
            "processing_summary": {
                "total_sources_attempted": len(self.processed_sources) + len(self.failed_sources),
                "successful_sources": len(self.processed_sources),
                "failed_sources": len(self.failed_sources),
                "total_articles_found": len(combined_content),
                "unique_articles_after_dedup": len(unique_content),
                "processing_timestamp": datetime.now().isoformat(),
                "source_details": self.processed_sources
            }
        }
        
        # Format final output
        final_output = self.formatter.format_output(unique_content, processing_metadata)
        
        # Validate against schema
        is_valid = self.formatter.validate_output(final_output)
        
        if not is_valid:
            logger.error("Output failed schema validation")
            return False
        
        # Save output
        success = self.formatter.save_output(final_output, output_path)
        
        if success:
            logger.info("🎉 Batch processing completed successfully!")
            logger.info(f"📊 Final stats: {len(unique_content)} unique articles from {len(self.processed_sources)} sources")
        
        return success
    
    def _deduplicate_content(self, content_list: List[ScrapedContent]) -> List[ScrapedContent]:
        """Remove duplicate content based on content hash"""
        
        seen_hashes = set()
        unique_content = []
        
        for content in content_list:
            if not content or not content.content:
                continue
            
            content_hash = hashlib.md5(content.content.encode('utf-8')).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_content.append(content)
            else:
                logger.debug(f"Duplicate content removed: {content.title[:50]}...")
        
        removed_count = len(content_list) - len(unique_content)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate articles")
        
        return unique_content


# Factory functions
def create_json_formatter(config: Dict, schema_path: Path = None) -> JSONFormatter:
    """Factory function to create JSON formatter"""
    return JSONFormatter(config, schema_path)

def create_batch_processor(config: Dict) -> BatchProcessor:
    """Factory function to create batch processor"""
    return BatchProcessor(config)