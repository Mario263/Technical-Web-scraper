# config/settings.py - Main configuration file

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Scraping settings - UNLIMITED MODE FOR MAXIMUM CONTENT
SCRAPING_CONFIG = {
    "request_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1,  # seconds
    "concurrent_requests": 8,  # More concurrent requests
    "rate_limit_delay": 1.5,  # Faster scraping
    "max_articles_per_source": 999,  # UNLIMITED - scrape everything available
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
}

# Content processing settings - MAXIMUM CONTENT CAPTURE
PROCESSING_CONFIG = {
    "min_content_length": 50,   # Accept even shorter content
    "max_content_length": 150000,  # Allow much longer articles
    "remove_elements": ["nav", "footer", "header", ".sidebar", ".advertisement", ".social-share"],
    "preserve_code_blocks": True,
    "preserve_links": True,
    "preserve_images": False
}

# Output settings
OUTPUT_CONFIG = {
    "team_id": "technical-content-team",
    "default_content_type": "blog",
    "include_metadata": True,
    "validate_schema": True
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "scraper.log"
}