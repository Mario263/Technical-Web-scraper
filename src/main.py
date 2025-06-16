# src/main.py - Main entry point for testing

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import LOGGING_CONFIG, SCRAPING_CONFIG, OUTPUT_DIR
import requests
import json

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG["file"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_basic_http():
    """Test basic HTTP functionality"""
    logger.info("Testing basic HTTP functionality...")
    
    try:
        # Test with a simple website first
        test_url = "https://httpbin.org/get"
        
        headers = {
            "User-Agent": SCRAPING_CONFIG["user_agents"][0]
        }
        
        response = requests.get(
            test_url, 
            headers=headers, 
            timeout=SCRAPING_CONFIG["request_timeout"]
        )
        
        if response.status_code == 200:
            logger.info("✅ Basic HTTP test successful!")
            logger.info(f"Response status: {response.status_code}")
            return True
        else:
            logger.error(f"❌ HTTP test failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ HTTP test failed with exception: {str(e)}")
        return False

def test_target_site_accessibility():
    """Test if our target sites are accessible"""
    logger.info("Testing target site accessibility...")
    
    test_urls = [
        "https://interviewing.io/blog",
        "https://nilmamano.com/blog/category/dsa"
    ]
    
    headers = {
        "User-Agent": SCRAPING_CONFIG["user_agents"][0]
    }
    
    results = {}
    
    for url in test_urls:
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=SCRAPING_CONFIG["request_timeout"]
            )
            
            results[url] = {
                "status_code": response.status_code,
                "accessible": response.status_code == 200,
                "content_length": len(response.text)
            }
            
            if response.status_code == 200:
                logger.info(f"✅ {url} - Accessible (Status: {response.status_code})")
            else:
                logger.warning(f"⚠️ {url} - Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ {url} - Error: {str(e)}")
            results[url] = {
                "status_code": None,
                "accessible": False,
                "error": str(e)
            }
    
    return results

def save_test_results(results):
    """Save test results to output directory"""
    output_file = OUTPUT_DIR / "setup_test_results.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to: {output_file}")

def main():
    """Main function to run setup tests"""
    logger.info("🚀 Starting Technical Content Scraper Setup Tests")
    logger.info("=" * 60)
    
    # Test 1: Basic HTTP functionality
    http_test = test_basic_http()
    
    # Test 2: Target site accessibility
    site_results = test_target_site_accessibility()
    
    # Compile results
    test_results = {
        "setup_timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
        )),
        "basic_http_test": http_test,
        "site_accessibility": site_results,
        "summary": {
            "total_sites_tested": len(site_results),
            "accessible_sites": sum(1 for r in site_results.values() if r.get("accessible", False)),
            "setup_successful": http_test and any(r.get("accessible", False) for r in site_results.values())
        }
    }
    
    # Save results
    save_test_results(test_results)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("🎯 SETUP TEST SUMMARY:")
    logger.info(f"Basic HTTP Test: {'✅ PASS' if http_test else '❌ FAIL'}")
    logger.info(f"Sites Accessible: {test_results['summary']['accessible_sites']}/{test_results['summary']['total_sites_tested']}")
    logger.info(f"Overall Setup: {'✅ READY' if test_results['summary']['setup_successful'] else '❌ ISSUES'}")
    
    if test_results['summary']['setup_successful']:
        logger.info("🎉 Setup complete! Ready to proceed to Phase 2.")
        return True
    else:
        logger.error("🚨 Setup issues detected. Please resolve before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)