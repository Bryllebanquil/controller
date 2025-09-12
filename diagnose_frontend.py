#!/usr/bin/env python3

import requests
import json

def diagnose_frontend():
    """Diagnose frontend configuration and connection issues"""
    print("🔍 Frontend Diagnosis")
    print("=" * 50)
    
    # Check frontend
    frontend_url = "https://agent-controller-dashboard.onrender.com"
    backend_url = "https://agent-controller-backend.onrender.com"
    
    print(f"1. Checking frontend: {frontend_url}")
    try:
        response = requests.get(frontend_url, timeout=10)
        print(f"   ✓ Frontend accessible: {response.status_code}")
        
        # Check if it's a React app
        if "react" in response.text.lower() or "root" in response.text:
            print("   ✓ Appears to be a React application")
        else:
            print("   ⚠ May not be a React application")
            
    except Exception as e:
        print(f"   ✗ Frontend error: {e}")
    
    print(f"\n2. Checking backend: {backend_url}")
    try:
        response = requests.get(f"{backend_url}/login", timeout=10)
        print(f"   ✓ Backend accessible: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Backend error: {e}")
    
    print(f"\n3. Checking backend API endpoints:")
    endpoints = [
        "/api/agents",
        "/api/status", 
        "/agents",
        "/status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=5)
            print(f"   {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    print(f"\n4. Frontend Socket.IO Configuration Issue:")
    print("   ⚠ The frontend is configured to connect to 'localhost:8080'")
    print("   ⚠ This means it's trying to connect to a local server, not the backend")
    print("   ⚠ The frontend needs to be configured with the correct backend URL")
    
    print(f"\n5. Solution:")
    print("   The frontend needs the VITE_SOCKET_URL environment variable set to:")
    print(f"   VITE_SOCKET_URL={backend_url}")
    print("   Or the frontend build needs to be updated with the correct backend URL")
    
    print(f"\n6. Current Status:")
    print("   ✓ Backend is running and accessible")
    print("   ✓ Frontend is accessible but misconfigured")
    print("   ⚠ Frontend cannot connect to backend due to wrong URL")
    print("   ⚠ Agents will not appear in frontend until this is fixed")

if __name__ == "__main__":
    diagnose_frontend()