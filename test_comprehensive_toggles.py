import requests
import json

# Comprehensive toggle functionality testing
base_url = "http://127.0.0.1:8080"

def test_scenario_1_global_bypasses():
    """Test global bypasses without agent selection"""
    print("=== Scenario 1: Global Bypasses (No Agent) ===")
    
    # Test global bypass toggle
    data = {
        "key": "fodhelper",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=data)
        result = response.json()
        print(f"Global bypass toggle: {result.get('success', False)}")
        return result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_scenario_2_agent_bypasses():
    """Test agent-specific bypasses"""
    print("\n=== Scenario 2: Agent-Specific Bypasses ===")
    
    # Test agent bypass toggle
    data = {
        "agent_id": "test-agent-456",
        "key": "eventvwr",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=data)
        result = response.json()
        print(f"Agent bypass toggle: {result.get('success', False)}")
        
        # Check if agent-specific data is present
        methods = result.get('methods', [])
        agent_method = next((m for m in methods if m['key'] == 'eventvwr'), None)
        if agent_method:
            print(f"Agent method status: {agent_method.get('enabled', False)}")
            return agent_method.get('enabled', False)
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_scenario_3_registry_without_admin():
    """Test registry operations without admin privileges"""
    print("\n=== Scenario 3: Registry Without Admin ===")
    
    # Test registry toggle without admin - use a fresh agent ID
    data = {
        "agent_id": "fresh-agent-no-admin-456",
        "key": "notify_center_hklm",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/registry/toggle", json=data)
        result = response.json()
        
        if response.status_code == 403 and result.get('need_admin'):
            print("✓ Registry blocked without admin privileges")
            return True
        else:
            print(f"✗ Registry allowed without admin (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_scenario_4_registry_with_admin():
    """Test registry operations with admin privileges"""
    print("\n=== Scenario 4: Registry With Admin ===")
    
    # First set admin privileges - use a different agent ID
    admin_data = {
        "agent_id": "agent-with-admin-789",
        "admin_enabled": True
    }
    
    try:
        # Set admin status
        admin_response = requests.post(f"{base_url}/api/system/agent/admin", json=admin_data)
        if admin_response.status_code != 200:
            print("Failed to set admin status")
            return False
            
        # Test registry toggle with admin
        registry_data = {
            "agent_id": "agent-with-admin-789",
            "key": "notify_center_hklm",
            "enabled": True
        }
        
        response = requests.post(f"{base_url}/api/system/registry/toggle", json=registry_data)
        result = response.json()
        
        if result.get('success'):
            print("✓ Registry allowed with admin privileges")
            return True
        else:
            print(f"✗ Registry blocked with admin")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_scenario_5_test_buttons():
    """Test test button functionality"""
    print("\n=== Scenario 5: Test Buttons ===")
    
    try:
        # Test bypass test
        bypass_test_data = {"key": "fodhelper"}
        bypass_response = requests.post(f"{base_url}/api/system/bypasses/test", json=bypass_test_data)
        bypass_result = bypass_response.json()
        
        # Test registry test
        registry_test_data = {"key": "notify_center_hklm"}
        registry_response = requests.post(f"{base_url}/api/system/registry/test", json=registry_test_data)
        registry_result = registry_response.json()
        
        bypass_ok = bypass_result.get('success', False) and 'result' in bypass_result
        registry_ok = registry_result.get('success', False) and 'result' in registry_result
        
        print(f"Bypass test: {'✓' if bypass_ok else '✗'}")
        print(f"Registry test: {'✓' if registry_ok else '✗'}")
        
        return bypass_ok and registry_ok
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_scenario_6_global_toggles():
    """Test global enable/disable toggles"""
    print("\n=== Scenario 6: Global Toggles ===")
    
    try:
        # Test global bypasses toggle
        bypass_data = {"global_enabled": True}
        bypass_response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=bypass_data)
        bypass_result = bypass_response.json()
        
        # Test global registry toggle
        registry_data = {"global_enabled": True}
        registry_response = requests.post(f"{base_url}/api/system/registry/toggle", json=registry_data)
        registry_result = registry_response.json()
        
        bypass_ok = bypass_result.get('success', False) and bypass_result.get('global_enabled', False)
        registry_ok = registry_result.get('success', False) and registry_result.get('global_enabled', False)
        
        print(f"Global bypasses: {'✓' if bypass_ok else '✗'}")
        print(f"Global registry: {'✓' if registry_ok else '✗'}")
        
        return bypass_ok and registry_ok
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Starting comprehensive toggle functionality tests...\n")
    
    results = []
    
    results.append(("Global Bypasses", test_scenario_1_global_bypasses()))
    results.append(("Agent-Specific Bypasses", test_scenario_2_agent_bypasses()))
    results.append(("Registry Without Admin", test_scenario_3_registry_without_admin()))
    results.append(("Registry With Admin", test_scenario_4_registry_with_admin()))
    results.append(("Test Buttons", test_scenario_5_test_buttons()))
    results.append(("Global Toggles", test_scenario_6_global_toggles()))
    
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All toggle functionality tests passed!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Review the results above.")