#!/usr/bin/env python3
"""Debug script to test crawling functionality directly"""

import asyncio
import sys
import json as json_module
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, '.')

from unified_server import crawl_data_single

async def test_crawl():
    """Test the crawling functionality directly"""
    try:
        print("Testing crawl_data_single function...")
        
        # Create a test request-like object
        class TestRequest:
            def __init__(self):
                self.url = "https://httpbin.org/html"
                self.auth_type = "none" 
                self.auth_token = None
                self.auth_username = None
                self.auth_password = None
                self.custom_headers = {}
                self.delay_seconds = 1.0
        
        request = TestRequest()
        
        # Test the single page crawl
        result = await crawl_data_single(request)
        
        print("Result:")
        print(json_module.dumps(result, indent=2))
        
        # Check for expected fields
        if result and isinstance(result, dict):
            print(f"Success: {result.get('success')}")
            print(f"Title: {result.get('title')}")
            print(f"Content length: {len(result.get('content', ''))}")
            print(f"Word count: {result.get('word_count')}")
            print(f"Method: {result.get('method')}")
        else:
            print("ERROR: Result is not a dictionary or is None")
            
    except Exception as e:
        print(f"ERROR in test_crawl: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crawl())