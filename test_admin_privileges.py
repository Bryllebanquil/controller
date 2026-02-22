import requests
import json

# Test admin privilege check for registry operations
base_url = "http://127.0.0.1:8080"

def test_registry_without_admin():
    print("Testing registry toggle without admin privileges...")
    data = {
        "agent_id": "test-agent-123",
        "key": "notify_center_hklm",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/registry/toggle", json=data)
        print(f"Registry toggle response: {response.status_code}")
        result = response.json()
        print(f"Response data: {result}")
        
        if result.get('need_admin'):
            print("✓ Admin privilege check working correctly!")
            return True
        else:
            print("✗ Admin privilege check not working")
            return False
            
    except Exception as e:
        print(f"Error testing registry toggle: {e}")
        return False

def test_registry_with_admin():
    print("\nTesting registry toggle with admin privileges...")
    
    # First set admin to true
    admin_data = {
        "agent_id": "test-agent-123",
        "admin_enabled": True
    }
    
    try:
        # Set admin status
        admin_response = requests.post(f"{base_url}/api/system/agent/admin", json=admin_data)
        if admin_response.status_code != 200:
            print("Failed to set admin status")
            return False
            
        # Now try registry toggle
        registry_data = {
            "agent_id": "test-agent-123",
            "key": "notify_center_hklm",
            "enabled": True
        }
        
        response = requests.post(f"{base_url}/api/system/registry/toggle", json=registry_data)
        print(f"Registry toggle response: {response.status_code}")
        result = response.json()
        print(f"Response data: {result}")
        
        if result.get('success'):
            print("✓ Registry toggle with admin working!")
            return True
        else:
            print("✗ Registry toggle with admin failed")
            return False
            
    except Exception as e:
        print(f"Error testing registry toggle with admin: {e}")
        return False

if __name__ == "__main__":
    print("Testing admin privilege functionality...")
    
    without_admin = test_registry_without_admin()
    with_admin = test_registry_with_admin()
    
    print(f"\nTest Results:")
    print(f"Without admin (should fail): {'✓' if without_admin else '✗'}")
    print(f"With admin (should succeed): {'✓' if with_admin else '✗'}")
    
    if without_admin and with_admin:
        print("\n✓ Admin privilege system working correctly!")
    else:
        print("\n✗ Admin privilege system has issues.")