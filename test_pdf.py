#!/usr/bin/env python3
"""
Test script for PDF parsing functionality
"""

import requests
import json

def test_pdf_parsing():
    """Test the PDF parsing endpoint"""
    url = "http://localhost:5000/api/pdf/parse"
    
    # Create a simple test PDF content for testing
    test_data = {
        'export_formats': 'json,md',
        'follow_links': 'false',
        'max_pages_from_links': '3'
    }
    
    print("Testing PDF parsing endpoint...")
    print(f"URL: {url}")
    print(f"Data: {test_data}")
    
    try:
        # Test the endpoint structure (without actual file)
        response = requests.post(url, data=test_data, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Endpoint correctly requires file upload (422 Unprocessable Entity)")
            return True
        else:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PDF endpoint: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_parsing()
    print(f"\nPDF parsing endpoint test: {'✅ PASSED' if success else '❌ FAILED'}")