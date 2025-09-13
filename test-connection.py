#!/usr/bin/env python3
"""
Connection test script for Neural Control Hub
Tests the connection between frontend and backend
"""

import requests
import json
import sys
import time
from urllib.parse import urljoin

def test_backend_connection(base_url="http://localhost:8080"):
    """Test backend API endpoints"""
    print(f"🔍 Testing backend connection to {base_url}")
    
    endpoints_to_test = [
        ("/api/auth/status", "GET"),
        ("/api/system/stats", "GET"),
        ("/api/agents", "GET"),
        ("/api/activity", "GET"),
    ]
    
    results = {}
    
    for endpoint, method in endpoints_to_test:
        try:
            url = urljoin(base_url, endpoint)
            print(f"  Testing {method} {endpoint}...")
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            if response.status_code == 200:
                print(f"    ✅ {endpoint} - OK")
                results[endpoint] = "success"
            else:
                print(f"    ⚠️  {endpoint} - HTTP {response.status_code}")
                results[endpoint] = f"http_{response.status_code}"
                
        except requests.exceptions.ConnectionError:
            print(f"    ❌ {endpoint} - Connection failed")
            results[endpoint] = "connection_failed"
        except requests.exceptions.Timeout:
            print(f"    ⏰ {endpoint} - Timeout")
            results[endpoint] = "timeout"
        except Exception as e:
            print(f"    ❌ {endpoint} - Error: {e}")
            results[endpoint] = f"error_{str(e)}"
    
    return results

def test_cors_headers(base_url="http://localhost:8080"):
    """Test CORS headers"""
    print(f"\n🌐 Testing CORS configuration...")
    
    try:
        # Test preflight request
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(urljoin(base_url, "/api/auth/status"), headers=headers, timeout=5)
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
        }
        
        print("  CORS Headers:")
        for header, value in cors_headers.items():
            if value:
                print(f"    ✅ {header}: {value}")
            else:
                print(f"    ❌ {header}: Not set")
        
        return cors_headers
        
    except Exception as e:
        print(f"    ❌ CORS test failed: {e}")
        return {}

def test_client_connection():
    """Test if client can connect to controller"""
    print(f"\n🤖 Testing client connection...")
    
    try:
        # Test if client.py can import required modules
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.append('.'); import client; print('Client imports successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("  ✅ Client imports successful")
            return True
        else:
            print(f"  ❌ Client import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Client test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Neural Control Hub Connection Test")
    print("=" * 50)
    
    # Test backend connection
    backend_results = test_backend_connection()
    
    # Test CORS
    cors_results = test_cors_headers()
    
    # Test client
    client_success = test_client_connection()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    success_count = sum(1 for result in backend_results.values() if result == "success")
    total_count = len(backend_results)
    
    print(f"Backend API Tests: {success_count}/{total_count} passed")
    print(f"Client Connection: {'✅ Passed' if client_success else '❌ Failed'}")
    
    if success_count == total_count and client_success:
        print("🎉 All tests passed! Complete system should work.")
        print("   Frontend ↔ Controller ↔ Client")
        return 0
    else:
        print("⚠️  Some tests failed. Check server and client status.")
        return 1

if __name__ == "__main__":
    sys.exit(main())