#!/usr/bin/env python3
"""
Basic functionality tests for the enhanced scraper
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all imports work"""
    try:
        from enhanced_scraper import ScrapedContent, EnhancedHTTPClient
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_scraped_content():
    """Test ScrapedContent class"""
    from enhanced_scraper import ScrapedContent
    
    content = ScrapedContent()
    content.title = "Test Article"
    content.content = "This is a test article with sufficient content to pass validation checks."
    
    assert content.is_valid(), "Valid content should pass validation"
    print("✅ ScrapedContent tests passed")
    return True

def main():
    """Run all tests"""
    print("🧪 Running Basic Tests")
    print("=" * 40)
    
    tests = [test_imports, test_scraped_content]
    passed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
