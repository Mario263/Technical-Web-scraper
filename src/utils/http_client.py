# src/utils/http_client.py - Robust HTTP client with retry logic

import requests
import time
import random
import logging
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse
import hashlib

logger = logging.getLogger(__name__)

class RobustHTTPClient:
    """HTTP client with retry logic, rate limiting, and user-agent rotation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.request_count = 0
        self.last_request_time = 0
        
        # Setup session defaults
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the config"""
        return random.choice(self.config["user_agents"])
    
    def _apply_rate_limiting(self):
        """Apply rate limiting between requests"""
        if self.last_request_time > 0:
            time_since_last = time.time() - self.last_request_time
            delay_needed = self.config["rate_limit_delay"] - time_since_last
            
            if delay_needed > 0:
                logger.debug(f"Rate limiting: sleeping for {delay_needed:.2f} seconds")
                time.sleep(delay_needed)
    
    def _should_retry(self, response: Optional[requests.Response], attempt: int) -> bool:
        """Determine if request should be retried"""
        if attempt >= self.config["retry_attempts"]:
            return False
        
        if response is None:
            return True
        
        # Retry on server errors or rate limiting
        if response.status_code in [429, 500, 502, 503, 504]:
            return True
        
        # Don't retry on client errors (except 429)
        if 400 <= response.status_code < 500:
            return False
        
        return False
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        base_delay = self.config["retry_delay"]
        max_delay = 60  # Maximum delay of 60 seconds
        
        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
        return min(delay, max_delay)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request with retry logic and rate limiting"""
        self._apply_rate_limiting()
        
        # Set random user agent for each request
        headers = kwargs.get('headers', {})
        headers['User-Agent'] = self._get_random_user_agent()
        kwargs['headers'] = headers
        
        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.config["request_timeout"]
        
        attempt = 0
        last_exception = None
        
        while attempt < self.config["retry_attempts"]:
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, **kwargs)
                self.last_request_time = time.time()
                self.request_count += 1
                
                # Log request details
                logger.info(f"GET {url} - Status: {response.status_code} - Size: {len(response.content)} bytes")
                
                if response.status_code == 200:
                    return response
                elif self._should_retry(response, attempt):
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"Request failed (status {response.status_code}), retrying in {delay:.2f}s")
                    time.sleep(delay)
                    attempt += 1
                else:
                    logger.error(f"Request failed with status {response.status_code}, not retrying")
                    return response
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request exception: {str(e)}")
                
                if self._should_retry(None, attempt):
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"Request failed with exception, retrying in {delay:.2f}s")
                    time.sleep(delay)
                    attempt += 1
                else:
                    logger.error(f"Request failed with exception, not retrying: {str(e)}")
                    raise e
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise requests.exceptions.RequestException(f"All retry attempts failed for {url}")
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        return {
            "total_requests": self.request_count,
            "session_active": True
        }
    
    def close(self):
        """Close the session"""
        self.session.close()
        logger.info(f"HTTP client closed. Total requests made: {self.request_count}")


class ContentCache:
    """Simple in-memory cache for HTTP responses"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def _generate_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[str]:
        """Get cached content for URL"""
        key = self._generate_key(url)
        if key in self.cache:
            self.access_times[key] = time.time()
            logger.debug(f"Cache HIT for {url}")
            return self.cache[key]
        
        logger.debug(f"Cache MISS for {url}")
        return None
    
    def put(self, url: str, content: str):
        """Cache content for URL"""
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        key = self._generate_key(url)
        self.cache[key] = content
        self.access_times[key] = time.time()
        logger.debug(f"Cached content for {url} ({len(content)} chars)")
    
    def _evict_oldest(self):
        """Remove oldest cache entry"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
        logger.debug("Evicted oldest cache entry")
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size
        }


# Factory function to create HTTP client
def create_http_client(config: Dict) -> RobustHTTPClient:
    """Factory function to create configured HTTP client"""
    logger.info("Creating HTTP client with retry logic and rate limiting")
    return RobustHTTPClient(config)