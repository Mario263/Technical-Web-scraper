#!/usr/bin/env python3
"""
Comprehensive Test Suite for Production Scraper

Tests all website scraping functionality and validates results.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from interactive_cli import UniversalWebScraper, EnhancedHTTPClient, SCRAPING_CONFIG, ScrapedContent, create_book_chapters

class ScraperTestSuite:
    """Comprehensive test suite for the scraper"""
    
    def __init__(self):
        self.client = EnhancedHTTPClient()
        self.scraper = UniversalWebScraper(self.client, SCRAPING_CONFIG)
        self.results = []
        
    def run_all_tests(self) -> Dict:
        """Run all tests and return results"""
        
        print("🧪 COMPREHENSIVE SCRAPER TEST SUITE")
        print("=" * 50)
        
        # Test sources
        test_sources = [
            {
                "name": "interviewing.io/blog",
                "url": "https://interviewing.io/blog",
                "expected_type": "interviewing_io_blog",
                "min_items": 5
            },
            {
                "name": "interviewing.io/topics",
                "url": "https://interviewing.io/topics",
                "expected_type": "interviewing_io_topics", 
                "min_items": 2
            },
            {
                "name": "interviewing.io/learn",
                "url": "https://interviewing.io/learn",
                "expected_type": "interviewing_io_learn",
                "min_items": 2
            },
            {
                "name": "nilmamano.com",
                "url": "https://nilmamano.com/blog/category/dsa",
                "expected_type": "nilmamano",
                "min_items": 3
            },
            {
                "name": "quill.co",
                "url": "https://quill.co/blog",
                "expected_type": "quill",
                "min_items": 1
            },
            {
                "name": "shreycation.substack.com",
                "url": "https://shreycation.substack.com/archive?sort=new",
                "expected_type": "substack",
                "min_items": 2
            }
        ]
        
        # Run tests
        for i, test_case in enumerate(test_sources, 1):
            print(f"\n📄 [{i}/{len(test_sources)}] Testing: {test_case['name']}")
            result = self.test_source(test_case)
            self.results.append(result)
        
        # Test book chapters
        print(f"\n📚 Testing book chapters...")
        book_result = self.test_book_chapters()
        self.results.append(book_result)
        
        # Generate summary
        summary = self.generate_summary()
        
        return {
            "test_results": self.results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_source(self, test_case: Dict) -> Dict:
        """Test a single source"""
        
        result = {
            "name": test_case["name"],
            "url": test_case["url"],
            "expected_type": test_case["expected_type"],
            "min_items": test_case["min_items"],
            "status": "UNKNOWN",
            "items_found": 0,
            "error": None,
            "details": {}
        }
        
        try:
            # Test website type detection
            detected_type = self.scraper._detect_website_type(test_case["url"])
            result["details"]["detected_type"] = detected_type
            
            if detected_type != test_case["expected_type"]:
                print(f"   ⚠️  Type detection mismatch: expected {test_case['expected_type']}, got {detected_type}")
            
            # Test scraping (limit to 5 items for speed)
            content = self.scraper.scrape_website(test_case["url"], max_pages=5)
            result["items_found"] = len(content) if content else 0
            
            # Validate content quality
            if content:
                valid_items = 0
                total_words = 0
                
                for item in content:
                    if item.is_valid():
                        valid_items += 1
                        total_words += item.metadata.get('word_count', 0)
                
                result["details"]["valid_items"] = valid_items
                result["details"]["total_words"] = total_words
                result["details"]["avg_words"] = total_words // max(1, valid_items)
                
                # Check if meets minimum requirements
                if valid_items >= test_case["min_items"]:
                    result["status"] = "PASS"
                    print(f"   ✅ PASS: {valid_items} valid items found")
                else:
                    result["status"] = "FAIL"
                    print(f"   ❌ FAIL: Only {valid_items} items found, need {test_case['min_items']}")
            else:
                result["status"] = "FAIL"
                print(f"   ❌ FAIL: No content found")
                
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            print(f"   ❌ ERROR: {str(e)}")
        
        return result
    
    def test_book_chapters(self) -> Dict:
        """Test book chapter generation"""
        
        result = {
            "name": "book_chapters",
            "url": "N/A",
            "expected_type": "book",
            "min_items": 8,
            "status": "UNKNOWN",
            "items_found": 0,
            "error": None,
            "details": {}
        }
        
        try:
            chapters = create_book_chapters()
            result["items_found"] = len(chapters)
            
            if chapters and len(chapters) == 8:
                # Validate chapter quality
                valid_chapters = 0
                for chapter in chapters:
                    if (chapter.is_valid() and 
                        chapter.author == "Aline Lerner" and
                        chapter.metadata.get('content_type') == 'book'):
                        valid_chapters += 1
                
                result["details"]["valid_chapters"] = valid_chapters
                
                if valid_chapters == 8:
                    result["status"] = "PASS"
                    print(f"   ✅ PASS: All 8 chapters generated successfully")
                else:
                    result["status"] = "FAIL"
                    print(f"   ❌ FAIL: Only {valid_chapters}/8 chapters are valid")
            else:
                result["status"] = "FAIL"
                print(f"   ❌ FAIL: Expected 8 chapters, got {len(chapters) if chapters else 0}")
                
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            print(f"   ❌ ERROR: {str(e)}")
        
        return result
    
    def generate_summary(self) -> Dict:
        """Generate test summary"""
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        
        success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
        
        # Calculate total items found
        total_items = sum(r["items_found"] for r in self.results)
        
        summary = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": success_rate,
            "total_items_found": total_items
        }
        
        print(f"\n{'='*50}")
        print("📊 TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🚨 Errors: {errors}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"📄 Total Items Found: {total_items}")
        print(f"{'='*50}")
        
        return summary
    
    def save_test_results(self, output_dir: Path):
        """Save test results to file"""
        
        output_dir.mkdir(exist_ok=True, parents=True)
        
        results = {
            "test_results": self.results,
            "summary": self.generate_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file = output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Test results saved to: {output_file}")
        return output_file
    
    def close(self):
        """Clean up resources"""
        self.client.close()


def main():
    """Run test suite"""
    
    print("🎯 Starting Production Scraper Test Suite")
    
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce log noise during tests
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_suite = ScraperTestSuite()
    
    try:
        # Run tests
        results = test_suite.run_all_tests()
        
        # Save results
        output_dir = Path(__file__).parent / "output"
        test_suite.save_test_results(output_dir)
        
        # Determine exit code
        success_rate = results["summary"]["success_rate"]
        
        if success_rate >= 80:
            print("\n🎉 TEST SUITE PASSED!")
            print("✅ System is ready for production use!")
            exit_code = 0
        else:
            print("\n❌ TEST SUITE FAILED!")
            print("🔧 Please review and fix issues before production use")
            exit_code = 1
        
        return exit_code
        
    except Exception as e:
        print(f"\n❌ Test suite crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        test_suite.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
