import requests
import json

# Debug the admin privilege system
base_url = "http://127.0.0.1:8080"

def debug_admin_system():
    agent_id = "test-agent-debug"
    
    print(f"=== Debugging admin system for agent: {agent_id} ===")
    
    # Step 1: Check current admin status (should be False by default)
    print("\n1. Checking default admin status...")
    
    # Step 2: Try registry toggle without admin (should fail)
    print("\n2. Testing registry toggle without admin...")
    registry_data = {
        "agent_id": agent_id,
        "key": "notify_center_hklm",
        "enabled": True
    }
    
    response = requests.post(f"{base_url}/api/system/registry/toggle", json=registry_data)
    print(f"Response status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 403 and result.get('need_admin'):
        print("✓ Admin check working correctly!")
    else:
        print("✗ Admin check not working")
        
    # Step 3: Set admin status to True
    print("\n3. Setting admin status to True...")
    admin_data = {
        "agent_id": agent_id,
        "admin_enabled": True
    }
    
    admin_response = requests.post(f"{base_url}/api/system/agent/admin", json=admin_data)
    print(f"Admin set response: {admin_response.status_code}")
    if admin_response.status_code == 200:
        admin_result = admin_response.json()
        print(f"Admin result: {json.dumps(admin_result, indent=2)}")
    
    # Step 4: Try registry toggle with admin (should succeed)
    print("\n4. Testing registry toggle with admin...")
    response = requests.post(f"{base_url}/api/system/registry/toggle", json=registry_data)
    print(f"Response status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200 and result.get('success'):
        print("✓ Registry toggle with admin working!")
    else:
        print("✗ Registry toggle with admin failed")

if __name__ == "__main__":
    debug_admin_system()