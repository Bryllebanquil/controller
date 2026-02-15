import requests
import json

# Debug registry admin check specifically
base_url = "http://127.0.0.1:8080"

def debug_registry_admin_check():
    print("=== Debugging Registry Admin Check ===")
    
    # Use a fresh agent ID that definitely doesn't have admin
    agent_id = "fresh-agent-no-admin-123"
    
    print(f"Testing with agent: {agent_id}")
    
    # First, check current admin status
    print("\n1. Checking current admin status...")
    # Since we don't have a GET endpoint, let's assume it's false for a new agent
    
    # Test registry toggle without setting admin
    print("\n2. Testing registry toggle without admin...")
    registry_data = {
        "agent_id": agent_id,
        "key": "notify_center_hklm",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/registry/toggle", json=registry_data)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("❌ Registry toggle succeeded - this should have failed!")
                return False
            else:
                print("✓ Registry toggle failed as expected")
                return True
        elif response.status_code == 403:
            print("✓ Registry blocked with 403 - admin check working!")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    debug_registry_admin_check()