#!/usr/bin/env python3
"""
Test script to check if the dashboard UI is working properly
"""

import os
import sys
import requests
import time

def test_dashboard_access():
    """Test if the dashboard is accessible and shows UI"""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Dashboard UI Access")
    print("=" * 40)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the server first:")
        print("   python3 start-backend.py")
        return False
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False
    
    # Test 2: Check login page
    try:
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code == 200:
            print("✅ Login page accessible")
            if "Admin Authentication Required" in response.text:
                print("✅ Login page shows authentication form")
            else:
                print("⚠️  Login page content unexpected")
        else:
            print(f"❌ Login page failed (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Login page test failed: {e}")
    
    # Test 3: Check if UI build files exist
    ui_path = "agent-controller ui v2.1/build/index.html"
    if os.path.exists(ui_path):
        print("✅ UI build files exist")
        
        # Check if assets exist
        assets_path = "agent-controller ui v2.1/build/assets"
        if os.path.exists(assets_path):
            assets = os.listdir(assets_path)
            print(f"✅ UI assets exist ({len(assets)} files)")
            for asset in assets:
                print(f"   - {asset}")
        else:
            print("❌ UI assets directory missing")
    else:
        print("❌ UI build files missing")
        return False
    
    # Test 4: Test authentication flow
    print("\n🔐 Testing Authentication Flow")
    print("-" * 30)
    
    # Check if ADMIN_PASSWORD is set
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        print("❌ ADMIN_PASSWORD environment variable not set")
        print("   Set it with: export ADMIN_PASSWORD='your_password'")
        return False
    else:
        print(f"✅ ADMIN_PASSWORD is set (length: {len(admin_password)})")
    
    # Test login
    try:
        session = requests.Session()
        login_data = {"password": admin_password}
        response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        
        if response.status_code == 302:
            print("✅ Login successful (redirected)")
            
            # Test dashboard access
            dashboard_response = session.get(f"{base_url}/dashboard")
            if dashboard_response.status_code == 200:
                print("✅ Dashboard accessible after login")
                
                # Check if it's serving the React app
                if "Advanced UAC Bypass Tool" in dashboard_response.text:
                    print("✅ Dashboard shows React UI")
                elif "root" in dashboard_response.text:
                    print("✅ Dashboard shows React container")
                else:
                    print("⚠️  Dashboard content unexpected")
                    print(f"   Response length: {len(dashboard_response.text)} chars")
                    print(f"   First 200 chars: {dashboard_response.text[:200]}")
            else:
                print(f"❌ Dashboard access failed (status: {dashboard_response.status_code})")
        else:
            print(f"❌ Login failed (status: {response.status_code})")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
    
    # Test 5: Check API endpoints
    print("\n🔌 Testing API Endpoints")
    print("-" * 25)
    
    try:
        session = requests.Session()
        login_data = {"password": admin_password}
        session.post(f"{base_url}/login", data=login_data)
        
        # Test auth status API
        auth_response = session.get(f"{base_url}/api/auth/status")
        if auth_response.status_code == 200:
            print("✅ Auth status API working")
        else:
            print(f"❌ Auth status API failed (status: {auth_response.status_code})")
        
        # Test agents API
        agents_response = session.get(f"{base_url}/api/agents")
        if agents_response.status_code == 200:
            print("✅ Agents API working")
        else:
            print(f"❌ Agents API failed (status: {agents_response.status_code})")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Dashboard UI Test Complete")
    return True

if __name__ == "__main__":
    test_dashboard_access()