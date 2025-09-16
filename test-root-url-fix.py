#!/usr/bin/env python3
"""
Test Root URL Fix
=================

Tests all the endpoints to verify the root URL issue is resolved.
"""

import requests
import time
import sys
from urllib.parse import urljoin

CONTROLLER_URL = 'https://agent-controller-backend.onrender.com'

def test_endpoint(endpoint, expected_status=200, description=""):
    """Test a single endpoint"""
    url = urljoin(CONTROLLER_URL, endpoint)
    print(f"🔍 Testing {endpoint:<20} - {description}")
    
    try:
        response = requests.get(url, timeout=15, allow_redirects=False)
        status = response.status_code
        content_length = len(response.text)
        
        if status == expected_status:
            print(f"   ✅ {status} OK ({content_length:,} bytes)")
            return True
        elif status in [301, 302, 307, 308]:  # Redirects
            location = response.headers.get('Location', 'Unknown')
            print(f"   🔄 {status} Redirect → {location}")
            return True
        elif status in [200, 201, 202]:  # Success codes
            print(f"   ✅ {status} Success ({content_length:,} bytes)")
            return True
        else:
            print(f"   ⚠️  {status} Unexpected ({content_length:,} bytes)")
            if content_length < 500:  # Show small responses
                print(f"      Content: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout after 15 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_login_flow():
    """Test the complete login flow"""
    print(f"\n🔐 Testing Login Flow")
    print("-" * 40)
    
    session = requests.Session()
    
    # Step 1: Get login page
    print("1. Getting login page...")
    try:
        login_response = session.get(f"{CONTROLLER_URL}/simple-login", timeout=10)
        if login_response.status_code == 200:
            print("   ✅ Login page loaded")
        else:
            print(f"   ❌ Login page failed: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Login page error: {e}")
        return False
    
    # Step 2: Submit login
    print("2. Submitting login form...")
    try:
        login_data = {'password': 'q'}
        post_response = session.post(f"{CONTROLLER_URL}/login", data=login_data, timeout=10, allow_redirects=False)
        
        if post_response.status_code in [302, 301]:
            print("   ✅ Login successful (redirect received)")
            
            # Step 3: Follow redirect
            print("3. Following redirect...")
            final_response = session.get(f"{CONTROLLER_URL}/", timeout=10)
            if final_response.status_code == 200:
                print("   ✅ Dashboard loaded after login")
                return True
            else:
                print(f"   ❌ Dashboard failed: {final_response.status_code}")
                return False
        else:
            print(f"   ❌ Login failed: {post_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Login flow error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Root URL Fix - Neural Control Hub")
    print("=" * 60)
    print(f"Target: {CONTROLLER_URL}")
    print("=" * 60)
    
    # Test all endpoints
    endpoints = [
        ('/', 'Root page (should redirect or show content)'),
        ('/test', 'Test page (should work)'),
        ('/simple-login', 'Simple login page'),
        ('/login', 'Full login page'), 
        ('/health', 'Health check'),
        ('/debug/status', 'Debug status'),
        ('/debug/dashboard', 'Debug dashboard'),
        ('/debug/login-test', 'Quick login test'),
        ('/dashboard', 'Main dashboard'),
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        result = test_endpoint(endpoint, description=description)
        results[endpoint] = result
        time.sleep(0.5)  # Brief pause between requests
    
    # Test login flow
    login_success = test_login_flow()
    results['login_flow'] = login_success
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for endpoint, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {endpoint}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The root URL should now work.")
    else:
        print("⚠️  Some tests failed. Check the specific endpoints above.")
    
    print("\n🔧 RECOMMENDED NEXT STEPS:")
    print("1. Visit https://agent-controller-backend.onrender.com/test")
    print("2. Try the simple login: https://agent-controller-backend.onrender.com/simple-login")
    print("3. Use password: 'q' (just the letter q)")
    print("4. Check debug dashboard: https://agent-controller-backend.onrender.com/debug/dashboard")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test crashed: {e}")
        sys.exit(1)