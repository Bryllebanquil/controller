import requests
import json

# Test the admin endpoint
base_url = "http://127.0.0.1:8080"

# Test admin status endpoint
def test_admin_endpoint():
    print("Testing admin endpoint...")
    data = {
        "agent_id": "test-agent-123",
        "admin_enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/agent/admin", json=data)
        print(f"Admin endpoint response: {response.status_code}")
        print(f"Response data: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing admin endpoint: {e}")
        return False

# Test bypass toggle endpoint
def test_bypass_toggle():
    print("\nTesting bypass toggle endpoint...")
    data = {
        "agent_id": "test-agent-123",
        "key": "test-bypass",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=data)
        print(f"Bypass toggle response: {response.status_code}")
        print(f"Response data: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing bypass toggle: {e}")
        return False

# Test registry toggle endpoint
def test_registry_toggle():
    print("\nTesting registry toggle endpoint...")
    data = {
        "agent_id": "test-agent-123",
        "key": "test-registry",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/registry/toggle", json=data)
        print(f"Registry toggle response: {response.status_code}")
        print(f"Response data: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing registry toggle: {e}")
        return False

if __name__ == "__main__":
    print("Starting API endpoint tests...")
    
    admin_ok = test_admin_endpoint()
    bypass_ok = test_bypass_toggle()
    registry_ok = test_registry_toggle()
    
    print(f"\nTest Results:")
    print(f"Admin endpoint: {'✓' if admin_ok else '✗'}")
    print(f"Bypass toggle: {'✓' if bypass_ok else '✗'}")
    print(f"Registry toggle: {'✓' if registry_ok else '✗'}")
    
    if admin_ok and bypass_ok and registry_ok:
        print("\n✓ All endpoints are working correctly!")
    else:
        print("\n✗ Some endpoints have issues.")