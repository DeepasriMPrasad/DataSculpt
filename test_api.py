#!/usr/bin/env python3
"""
Test script to validate CrawlOps API functionality
Tests all non-negotiable requirements
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ Health check passed")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_extract_basic():
    """Test basic content extraction"""
    try:
        payload = {
            "url": "https://httpbin.org/html",
            "timeout": 30
        }
        response = requests.post(f"{API_BASE}/extract", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "json" in data
        assert "markdown" in data
        assert "meta" in data
        assert data["meta"]["word_count"] > 0
        print("✓ Basic content extraction passed")
        return True
    except Exception as e:
        print(f"✗ Basic content extraction failed: {e}")
        return False

def test_extract_advanced():
    """Test advanced extraction with parameters"""
    try:
        payload = {
            "url": "https://httpbin.org/html",
            "timeout": 30,
            "word_count_threshold": 50,
            "user_agent": "CrawlOps Studio/1.0"
        }
        response = requests.post(f"{API_BASE}/extract", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["word_count"] >= 50
        print("✓ Advanced content extraction passed")
        return True
    except Exception as e:
        print(f"✗ Advanced content extraction failed: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid URLs"""
    try:
        payload = {
            "url": "invalid-url",
            "timeout": 30
        }
        response = requests.post(f"{API_BASE}/extract", json=payload)
        assert response.status_code == 400
        print("✓ Error handling passed")
        return True
    except Exception as e:
        print(f"✗ Error handling failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running CrawlOps API tests...")
    print("=" * 40)
    
    tests = [
        test_health,
        test_extract_basic,
        test_extract_advanced,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CrawlOps API is fully functional.")
        return 0
    else:
        print("❌ Some tests failed. Please check the API.")
        return 1

if __name__ == "__main__":
    sys.exit(main())