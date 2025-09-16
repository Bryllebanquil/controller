#!/usr/bin/env python3
"""
Test Dashboard Fix
==================

Tests the dashboard endpoints to ensure they work properly.
"""

import requests
import time
import sys

CONTROLLER_URL = 'https://agent-controller-backend.onrender.com'

def test_endpoints():
    print("🧪 Testing Controller Endpoints")
    print("=" * 50)
    
    endpoints_to_test = [
        ('/health', 'Health Check'),
        ('/debug/status', 'Debug Status'),
        ('/debug/dashboard', 'Debug Dashboard'),
        ('/login', 'Login Page'),
        ('/', 'Root Page'),
        ('/dashboard', 'Dashboard Page')
    ]
    
    results = {}
    
    for endpoint, name in endpoints_to_test:
        print(f"\n🔍 Testing {name}: {CONTROLLER_URL}{endpoint}")
        try:
            response = requests.get(f"{CONTROLLER_URL}{endpoint}", timeout=10)
            status = response.status_code
            content_length = len(response.text)
            
            if status == 200:
                print(f"✅ {name}: {status} OK ({content_length} bytes)")
                results[endpoint] = 'PASS'
            elif status in [302, 301]:  # Redirects
                print(f"🔄 {name}: {status} Redirect to {response.headers.get('Location', 'Unknown')}")
                results[endpoint] = 'REDIRECT'
            else:
                print(f"⚠️  {name}: {status} ({content_length} bytes)")
                results[endpoint] = f'STATUS_{status}'
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results[endpoint] = 'ERROR'
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 ENDPOINT TEST SUMMARY")
    print("=" * 50)
    
    for endpoint, name in endpoints_to_test:
        result = results.get(endpoint, 'UNKNOWN')
        status_emoji = {
            'PASS': '✅',
            'REDIRECT': '🔄',
            'ERROR': '❌'
        }.get(result, '⚠️')
        
        print(f"{status_emoji} {name:<20} {endpoint:<20} {result}")
    
    print("\n🎯 KEY ENDPOINTS TO TEST:")
    print(f"   • Debug Dashboard: {CONTROLLER_URL}/debug/dashboard")
    print(f"   • Login Page: {CONTROLLER_URL}/login (password: 'q')")
    print(f"   • Debug Status: {CONTROLLER_URL}/debug/status")
    print(f"   • Health Check: {CONTROLLER_URL}/health")

if __name__ == "__main__":
    test_endpoints()