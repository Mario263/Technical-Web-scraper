#!/usr/bin/env python3
"""
Quick Setup and Verification Script

This script verifies that everything is working correctly.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run setup verification"""
    
    print("🔧 Production Scraper Setup Verification")
    print("=" * 50)
    
    project_dir = Path(__file__).parent
    
    # Check Python version
    print("1. 🐍 Checking Python version...")
    if sys.version_info >= (3, 8):
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor} - OK")
    else:
        print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} - Need 3.8+")
        return False
    
    # Check dependencies
    print("\n2. 📦 Checking dependencies...")
    try:
        import requests
        import bs4
        print("   ✅ Core dependencies - OK")
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        print("   💡 Run: pip install -r requirements.txt")
        return False
    
    # Check files
    print("\n3. 📁 Checking project files...")
    required_files = [
        "interactive_cli.py",
        "test_all_sources.py",
        "requirements.txt",
        "README.md"
    ]
    
    for file in required_files:
        if (project_dir / file).exists():
            print(f"   ✅ {file} - Found")
        else:
            print(f"   ❌ {file} - Missing")
            return False
    
    # Check directories
    required_dirs = ["output", "logs"]
    for dir_name in required_dirs:
        dir_path = project_dir / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/ - Found")
        else:
            print(f"   📁 {dir_name}/ - Creating...")
            dir_path.mkdir(exist_ok=True)
    
    # Test import
    print("\n4. 🧪 Testing imports...")
    try:
        sys.path.insert(0, str(project_dir))
        from interactive_cli import UniversalWebScraper, EnhancedHTTPClient
        print("   ✅ Main modules - OK")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 SETUP VERIFICATION COMPLETE!")
    print("=" * 50)
    print("✅ System is ready for production use!")
    print("\n🚀 Next steps:")
    print("   1. Run interactive mode: python interactive_cli.py")
    print("   2. Run tests: python test_all_sources.py")
    print("   3. Run Aline assignment: python interactive_cli.py --aline")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
