#!/usr/bin/env python3
"""
Interactive CLI Tool for Universal Web Scraping

This tool allows users to scrape ANY website interactively through a command-line interface.
It automatically detects website types and extracts content in the standardized format.
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import SCRAPING_CONFIG, OUTPUT_DIR, LOGS_DIR
from src.utils.http_client import create_http_client
from src.scrapers.universal.universal_scraper import UniversalWebScraper
from src.processors.pdf_processor import create_pdf_processor


class InteractiveScraper:
    """Interactive command-line web scraper"""
    
    def __init__(self):
        self.setup_logging()
        self.client = create_http_client(SCRAPING_CONFIG)
        self.scraper = UniversalWebScraper(self.client, SCRAPING_CONFIG)
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """Setup logging for interactive mode"""
        log_file = LOGS_DIR / f"interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_interactive_mode(self):
        """Run interactive scraping session"""
        
        self.print_banner()
        
        while True:
            try:
                print("\n" + "="*60)
                print("🌐 UNIVERSAL WEB SCRAPER")
                print("="*60)
                
                # Get user input
                choice = self.get_user_choice()
                
                if choice == 'quit':
                    print("👋 Thanks for using the Universal Web Scraper!")
                    break
                elif choice == 'scrape':
                    self.scrape_website_interactive()
                elif choice == 'batch':
                    self.batch_scrape_interactive()
                elif choice == 'aline':
                    self.run_aline_assignment()
                elif choice == 'test':
                    self.run_test_suite()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {str(e)}")
                self.logger.error(f"Interactive mode error: {str(e)}")
    
    def print_banner(self):
        """Print welcome banner"""
        
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    UNIVERSAL WEB SCRAPER                     ║
║                                                              ║
║  🌐 Scrape ANY website automatically                        ║
║  📊 Standardized JSON output format                         ║
║  🔍 Intelligent content detection                           ║
║  ⚡ High-quality content filtering                          ║
║                                                              ║
║  Supports: Blogs, Substack, Documentation, News sites       ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def get_user_choice(self) -> str:
        """Get user's choice for what to do"""
        
        print("\n📋 What would you like to do?")
        print("   1. 🌐 Scrape a single website")
        print("   2. 📚 Batch scrape multiple websites")
        print("   3. 🎯 Run Aline Assignment (all required sources)")
        print("   4. 🧪 Run test suite")
        print("   5. 🚪 Quit")
        
        while True:
            choice = input("\n➤ Enter your choice (1-5): ").strip()
            
            if choice == '1':
                return 'scrape'
            elif choice == '2':
                return 'batch'
            elif choice == '3':
                return 'aline'
            elif choice == '4':
                return 'test'
            elif choice == '5':
                return 'quit'
            else:
                print("❌ Invalid choice. Please enter 1-5.")
    
    def scrape_website_interactive(self):
        """Interactive single website scraping"""
        
        print("\n🌐 SINGLE WEBSITE SCRAPER")
        print("-" * 40)
        
        # Get URL
        url = input("➤ Enter the website URL to scrape: ").strip()
        if not url:
            print("❌ No URL provided.")
            return
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Get max pages
        try:
            max_pages_input = input("➤ Max pages to scrape (press Enter for no limit): ").strip()
            max_pages = int(max_pages_input) if max_pages_input else None
        except ValueError:
            print("❌ Invalid number. Using no limit.")
            max_pages = None
        
        # Get team ID
        team_id = input("➤ Team ID (optional, default: 'user_session'): ").strip()
        if not team_id:
            team_id = 'user_session'
        
        print(f"\n🔄 Starting scrape of: {url}")
        if max_pages:
            print(f"📊 Limited to {max_pages} pages")
        
        try:
            # Scrape the website, with special handling for quill.co/blog
            if "quill.co/blog" in url:
                from src.scrapers.smart_quill_scraper import SmartQuillScraper
                smart_scraper = SmartQuillScraper()
                content = smart_scraper.scrape_quill_co()
            else:
                content = self.scraper.scrape_website(url, max_pages=max_pages)
            
            if not content:
                print("❌ No content found or website couldn't be scraped.")
                print("💡 This could be due to:")
                print("   • Anti-bot protection")
                print("   • No scrapeable content")
                print("   • Network issues")
                return
            
            # Convert to output format
            output = self.convert_to_output_format(content, team_id)
            
            # Save results
            filename = self.save_results(output, f"single_website_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Display summary
            self.display_scrape_summary(content, filename)
            
        except Exception as e:
            print(f"❌ Scraping failed: {str(e)}")
            self.logger.error(f"Scraping error for {url}: {str(e)}")
    
    def batch_scrape_interactive(self):
        """Interactive batch scraping"""
        
        print("\n📚 BATCH WEBSITE SCRAPER")
        print("-" * 40)
        
        urls = []
        print("➤ Enter website URLs (one per line, empty line to finish):")
        
        while True:
            url = input("   URL: ").strip()
            if not url:
                break
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            urls.append(url)
            print(f"   ✅ Added: {url}")
        
        if not urls:
            print("❌ No URLs provided.")
            return
        
        # Get settings
        try:
            max_pages_input = input("➤ Max pages per website (press Enter for no limit): ").strip()
            max_pages = int(max_pages_input) if max_pages_input else None
        except ValueError:
            max_pages = None
        
        team_id = input("➤ Team ID (optional, default: 'batch_session'): ").strip()
        if not team_id:
            team_id = 'batch_session'
        
        print(f"\n🔄 Starting batch scrape of {len(urls)} websites...")
        
        all_content = []
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\n📄 [{i}/{len(urls)}] Scraping: {url}")
            
            try:
                if "quill.co/blog" in url:
                    from src.scrapers.smart_quill_scraper import SmartQuillScraper
                    smart_scraper = SmartQuillScraper()
                    content = smart_scraper.scrape_quill_co()
                else:
                    content = self.scraper.scrape_website(url, max_pages=max_pages)
                if content:
                    all_content.extend(content)
                    successful += 1
                    print(f"   ✅ Success: {len(content)} items")
                else:
                    failed += 1
                    print(f"   ❌ No content found")
            
            except Exception as e:
                failed += 1
                print(f"   ❌ Failed: {str(e)}")
                self.logger.error(f"Batch scrape error for {url}: {str(e)}")
        
        if not all_content:
            print("❌ No content scraped from any website.")
            return
        
        # Convert and save
        output = self.convert_to_output_format(all_content, team_id)
        filename = self.save_results(output, f"batch_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Display summary
        print(f"\n📊 BATCH SCRAPE SUMMARY")
        print(f"   🌐 Websites attempted: {len(urls)}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📄 Total items: {len(all_content)}")
        print(f"   💾 Saved to: {filename}")
    
    def run_aline_assignment(self):
        """Run the complete Aline assignment"""
        
        print("\n🎯 ALINE ASSIGNMENT - COMPLETE SCRAPE")
        print("-" * 50)
        print("This will scrape ALL required sources:")
        print("  • interviewing.io/blog")
        print("  • interviewing.io/topics#companies")
        print("  • interviewing.io/learn#interview-guides")
        print("  • nilmamano.com/blog/category/dsa")
        print("  • quill.co/blog")
        print("  • shreycation.substack.com")
        print("  • Book chapters (8 chapters)")
        
        confirm = input("\n➤ Continue with full assignment? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Assignment cancelled.")
            return
        
        print("\n🔄 Starting comprehensive assignment...")
        
        try:
            # Run comprehensive scraper
            from complete_assignment_comprehensive import ComprehensiveAssignmentScraper
            
            scraper = ComprehensiveAssignmentScraper()
            success = scraper.run_comprehensive_assignment()
            
            if success:
                print("\n✅ Aline assignment completed successfully!")
                print("📁 Check output/aline_comprehensive_assignment.json for results")
                print("📊 Check output/comprehensive_summary.json for summary")
            else:
                print("\n❌ Assignment failed. Check logs for details.")
        
        except Exception as e:
            print(f"❌ Assignment failed: {str(e)}")
            self.logger.error(f"Aline assignment error: {str(e)}")
    
    def run_test_suite(self):
        """Run the test suite"""

        print("\n🧪 RUNNING TEST SUITE")
        print("-" * 30)

        confirm = input("➤ Run all tests including Quill.co? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Tests cancelled.")
            return

        try:
            from test_scraper import ScraperTestSuite
            from test_smart_quill import test_smart_quill

            test_suite = ScraperTestSuite()
            results = test_suite.run_all_tests()

            # Display standard test suite results
            summary = results.get('summary', {})
            print(f"\n📊 TEST RESULTS")
            print(f"   Total Tests: {summary.get('total_tests', 0)}")
            print(f"   ✅ Passed: {summary.get('passed', 0)}")
            print(f"   ❌ Failed: {summary.get('failed', 0)}")
            print(f"   📈 Success Rate: {summary.get('success_rate', 0):.1f}%")

            # Save standard test results
            output_dir = OUTPUT_DIR / "test_results"
            output_dir.mkdir(exist_ok=True, parents=True)
            test_suite.save_test_results(output_dir)

            # Run and report the Quill test
            print("\n🧪 Running Quill.co smart scraper test...")
            quill_success = test_smart_quill()
            if quill_success:
                print("✅ Quill.co scraper passed!")
            else:
                print("❌ Quill.co scraper failed.")

        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            self.logger.error(f"Test suite error: {str(e)}")
    
    def convert_to_output_format(self, content: List, team_id: str) -> dict:
        """Convert scraped content to standardized output format"""
        
        output = {
            "team_id": team_id,
            "items": []
        }
        
        for item in content:
            formatted_item = {
                "title": item.title or "Untitled",
                "content": item.content or "",
                "content_type": getattr(item, 'content_type', item.metadata.get('content_type', 'other')),
                "source_url": item.source_url or "",
                "author": item.author or "",
                "user_id": ""
            }
            output["items"].append(formatted_item)
        
        return output
    
    def save_results(self, output: dict, filename_prefix: str) -> Path:
        """Save results to JSON file"""
        
        filename = f"{filename_prefix}.json"
        output_file = OUTPUT_DIR / filename
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)
        
        return output_file
    
    def display_scrape_summary(self, content: List, filename: Path):
        """Display scraping summary"""
        
        print(f"\n📊 SCRAPING SUMMARY")
        print(f"   📄 Total items scraped: {len(content)}")
        
        # Content type breakdown
        content_types = {}
        total_words = 0
        
        for item in content:
            content_type = item.metadata.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
            total_words += len(item.content.split()) if item.content else 0
        
        print(f"   📝 Total words: {total_words:,}")
        print(f"   📊 Content types:")
        for content_type, count in content_types.items():
            print(f"      • {content_type}: {count}")
        
        print(f"   💾 Saved to: {filename}")
        
        # Quality metrics
        high_quality = sum(1 for item in content 
                          if item.metadata.get('quality_metrics', {}).get('quality_score', 0) > 0.5)
        print(f"   ⭐ High quality items: {high_quality}/{len(content)} ({high_quality/len(content)*100:.1f}%)")


def run_command_line():
    """Run command line interface"""
    
    parser = argparse.ArgumentParser(description='Universal Web Scraper')
    parser.add_argument('--url', help='Website URL to scrape')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape')
    parser.add_argument('--team-id', default='cli_session', help='Team ID for output')
    parser.add_argument('--output', help='Output filename (without extension)')
    parser.add_argument('--test', action='store_true', help='Run test suite')
    parser.add_argument('--aline', action='store_true', help='Run Aline assignment')
    
    args = parser.parse_args()
    
    # Create directories
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    LOGS_DIR.mkdir(exist_ok=True, parents=True)
    
    scraper = InteractiveScraper()
    
    if args.test:
        print("🧪 Running test suite...")
        scraper.run_test_suite()
    elif args.aline:
        print("🎯 Running Aline assignment...")
        scraper.run_aline_assignment()
    elif args.url:
        print(f"🌐 Scraping: {args.url}")
        
        try:
            content = scraper.scraper.scrape_website(args.url, max_pages=args.max_pages)
            
            if content:
                output = scraper.convert_to_output_format(content, args.team_id)
                
                filename = args.output or f"cli_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                output_file = scraper.save_results(output, filename)
                
                scraper.display_scrape_summary(content, output_file)
            else:
                print("❌ No content found.")
        
        except Exception as e:
            print(f"❌ Scraping failed: {str(e)}")
    else:
        # Run interactive mode
        scraper.run_interactive_mode()


def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        # Command line mode
        run_command_line()
    else:
        # Interactive mode
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        LOGS_DIR.mkdir(exist_ok=True, parents=True)
        
        scraper = InteractiveScraper()
        scraper.run_interactive_mode()


if __name__ == "__main__":
    main()
