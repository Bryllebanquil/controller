import requests
import json

# Debug test button functionality
base_url = "http://127.0.0.1:8080"

def debug_test_buttons():
    print("=== Debugging Test Buttons ===")
    
    try:
        # Test bypass test
        print("Testing bypass test endpoint...")
        bypass_test_data = {"key": "fodhelper"}
        bypass_response = requests.post(f"{base_url}/api/system/bypasses/test", json=bypass_test_data)
        print(f"Bypass test status: {bypass_response.status_code}")
        print(f"Bypass test response: {bypass_response.text}")
        
        if bypass_response.status_code == 200:
            bypass_result = bypass_response.json()
            print(f"Bypass test result: {bypass_result}")
            
        # Test registry test
        print("\nTesting registry test endpoint...")
        registry_test_data = {"key": "notify_center_hklm"}
        registry_response = requests.post(f"{base_url}/api/system/registry/test", json=registry_test_data)
        print(f"Registry test status: {registry_response.status_code}")
        print(f"Registry test response: {registry_response.text}")
        
        if registry_response.status_code == 200:
            registry_result = registry_response.json()
            print(f"Registry test result: {registry_result}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_test_buttons()