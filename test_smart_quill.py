#!/usr/bin/env python3

print("🧪 Testing Smart Quill.co Scraper...")

try:
    import sys
    sys.path.append('/Users/mario/Desktop/technical-content-scraper')
    
    from src.scrapers.smart_quill_scraper import test_smart_quill
    
    success = test_smart_quill()
    
    if success:
        print("\n🎉 SUCCESS! The smart scraper can extract quill.co content!")
        print("🔧 This uses content parsing instead of relying on HTML structure")
    else:
        print("\n❌ Still having issues with quill.co")
    
except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()
