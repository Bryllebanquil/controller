#!/usr/bin/env python3
"""
Security Test Script for Neural Control Hub
Tests the authentication and route protection features
"""

import requests
import hashlib
from urllib.parse import urljoin

def test_login_page():
    """Test that the login page is accessible"""
    print("Testing login page accessibility...")
    try:
        response = requests.get("http://localhost:8080/login")
        assert response.status_code == 200
        assert "Admin Authentication Required" in response.text
        print("✅ Login page accessible")
        return True
    except Exception as e:
        print(f"❌ Login page test failed: {e}")
        return False

def test_dashboard_protection():
    """Test that dashboard is protected without authentication"""
    print("Testing dashboard protection...")
    try:
        response = requests.get("http://localhost:8080/dashboard", allow_redirects=False)
        assert response.status_code == 302  # Should redirect to login
        print("✅ Dashboard properly protected")
        return True
    except Exception as e:
        print(f"❌ Dashboard protection test failed: {e}")
        return False

def test_successful_login():
    """Test successful login with correct password"""
    print("Testing successful login...")
    try:
        session = requests.Session()
        login_data = {"password": "admin123"}
        response = session.post("http://localhost:8080/login", data=login_data, allow_redirects=False)
        assert response.status_code == 302  # Should redirect to dashboard
        print("✅ Successful login test passed")
        return session
    except Exception as e:
        print(f"❌ Successful login test failed: {e}")
        return None

def test_dashboard_access(session):
    """Test dashboard access after successful login"""
    print("Testing dashboard access after login...")
    try:
        response = session.get("http://localhost:8080/dashboard")
        assert response.status_code == 200
        assert "NEURAL CONTROL HUB" in response.text
        print("✅ Dashboard access after login successful")
        return True
    except Exception as e:
        print(f"❌ Dashboard access test failed: {e}")
        return False

def test_logout(session):
    """Test logout functionality"""
    print("Testing logout functionality...")
    try:
        response = session.get("http://localhost:8080/logout", allow_redirects=False)
        assert response.status_code == 302  # Should redirect to login
        print("✅ Logout functionality working")
        return True
    except Exception as e:
        print(f"❌ Logout test failed: {e}")
        return False

def test_protected_endpoints():
    """Test that protected endpoints require authentication"""
    print("Testing protected endpoints...")
    protected_endpoints = [
        "/stream/test-agent",
        "/video_feed/test-agent",
        "/camera_feed/test-agent",
        "/audio_feed/test-agent"
    ]
    
    for endpoint in protected_endpoints:
        try:
            response = requests.get(f"http://localhost:8080{endpoint}", allow_redirects=False)
            assert response.status_code == 302  # Should redirect to login
            print(f"✅ {endpoint} properly protected")
        except Exception as e:
            print(f"❌ {endpoint} protection test failed: {e}")
            return False
    return True

def main():
    """Run all security tests"""
    print("🔒 Neural Control Hub Security Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server is not running. Please start the server first:")
        print("   ./start.sh")
        return
    
    tests = [
        test_login_page,
        test_dashboard_protection,
        lambda: test_successful_login(),
        lambda: test_dashboard_access(test_successful_login()),
        lambda: test_logout(test_successful_login()),
        test_protected_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Security Tests Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All security tests passed!")
    else:
        print("⚠️  Some security tests failed. Please review the implementation.")

if __name__ == "__main__":
    main()