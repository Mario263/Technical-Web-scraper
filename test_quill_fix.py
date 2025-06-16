#!/usr/bin/env python3

print("🧪 Testing quill.co fix...")

try:
    import sys
    sys.path.append('/Users/mario/Desktop/technical-content-scraper')
    
    from fixed_scraper import FixedAssignmentRunner
    
    runner = FixedAssignmentRunner()
    
    print("Testing quill.co specifically...")
    result = runner.test_quill_co_specifically()
    
    if result.get("items"):
        print(f"✅ SUCCESS: Found {len(result['items'])} items from quill.co")
        print("✅ These should be about data analytics, not office supplies!")
    else:
        print("❌ No items found")
    
except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()
