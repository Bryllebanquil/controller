import requests
import json

# Comprehensive error handling validation for all API endpoints
base_url = "http://127.0.0.1:8080"

def test_invalid_agent_id():
    """Test with invalid agent ID formats"""
    print("Testing invalid agent ID handling...")
    
    test_cases = [
        {"agent_id": None, "expected_error": "Missing agent_id"},
        {"agent_id": "", "expected_error": "Missing agent_id"},
        {"agent_id": 123, "expected_error": "Invalid agent_id format"},
        {"agent_id": [], "expected_error": "Invalid agent_id format"},
    ]
    
    results = []
    for test_case in test_cases:
        data = {
            "agent_id": test_case["agent_id"],
            "admin_enabled": True
        }
        
        try:
            response = requests.post(f"{base_url}/api/system/agent/admin", json=data, timeout=5)
            result = response.json()
            
            if response.status_code == 400 and result.get('error'):
                print(f"✓ Invalid agent_id {test_case['agent_id']} properly rejected: {result['error']}")
                results.append(True)
            else:
                print(f"✗ Invalid agent_id {test_case['agent_id']} not properly handled")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error testing invalid agent_id {test_case['agent_id']}: {e}")
            results.append(False)
        except Exception as e:
            print(f"✗ Error testing invalid agent_id {test_case['agent_id']}: {e}")
            results.append(False)
    
    return all(results)

def test_missing_required_fields():
    """Test with missing required fields"""
    print("\nTesting missing required fields...")
    
    endpoints = [
        ("/api/system/agent/admin", {}),
        ("/api/system/bypasses/toggle", {"key": "test"}),
        ("/api/system/registry/toggle", {"key": "test"}),
        ("/api/system/bypasses/test", {}),
        ("/api/system/registry/test", {}),
    ]
    
    results = []
    for endpoint, partial_data in endpoints:
        try:
            response = requests.post(f"{base_url}{endpoint}", json=partial_data)
            
            if response.status_code in [400, 403]:
                result = response.json()
                if result.get('error'):
                    print(f"✓ {endpoint} properly rejects incomplete data: {result['error']}")
                    results.append(True)
                else:
                    print(f"✗ {endpoint} missing error message")
                    results.append(False)
            else:
                print(f"✗ {endpoint} should reject incomplete data (got {response.status_code})")
                results.append(False)
                
        except Exception as e:
            print(f"✗ Error testing {endpoint}: {e}")
            results.append(False)
    
    return all(results)

def test_invalid_data_types():
    """Test with invalid data types"""
    print("\nTesting invalid data types...")
    
    test_cases = [
        ("/api/system/agent/admin", {"agent_id": "test", "admin_enabled": "not_boolean"}),
        ("/api/system/bypasses/toggle", {"agent_id": "test", "key": "test", "enabled": "not_boolean"}),
        ("/api/system/registry/toggle", {"agent_id": "test", "key": "test", "enabled": "not_boolean"}),
    ]
    
    results = []
    for endpoint, data in test_cases:
        try:
            response = requests.post(f"{base_url}{endpoint}", json=data)
            result = response.json()
            
            if response.status_code == 400 and "invalid" in result.get('error', '').lower():
                print(f"✓ {endpoint} properly rejects invalid data types")
                results.append(True)
            else:
                print(f"✗ {endpoint} should reject invalid data types")
                results.append(False)
                
        except Exception as e:
            print(f"✗ Error testing {endpoint}: {e}")
            results.append(False)
    
    return all(results)

def test_admin_privilege_edge_cases():
    """Test admin privilege edge cases"""
    print("\nTesting admin privilege edge cases...")
    
    # Test 1: Registry operation without admin
    print("  Test 1: Registry without admin privileges...")
    data_no_admin = {
        "agent_id": "no-admin-agent-789",
        "key": "notify_center_hklm",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/registry/toggle", json=data_no_admin)
        result = response.json()
        
        if response.status_code == 403 and result.get('need_admin'):
            print("    ✓ Registry properly blocked without admin")
            test1_passed = True
        else:
            print("    ✗ Registry should be blocked without admin")
            test1_passed = False
            
    except Exception as e:
        print(f"    ✗ Error testing registry without admin: {e}")
        test1_passed = False
    
    # Test 2: Registry operation with admin
    print("  Test 2: Registry with admin privileges...")
    
    # First set admin
    admin_data = {"agent_id": "has-admin-agent-789", "admin_enabled": True}
    try:
        admin_response = requests.post(f"{base_url}/api/system/agent/admin", json=admin_data)
        if admin_response.status_code != 200:
            print("    ✗ Failed to set admin status")
            test2_passed = False
        else:
            # Now try registry
            registry_data = {
                "agent_id": "has-admin-agent-789",
                "key": "notify_center_hklm",
                "enabled": True
            }
            
            response = requests.post(f"{base_url}/api/system/registry/toggle", json=registry_data)
            result = response.json()
            
            if response.status_code == 200 and result.get('success'):
                print("    ✓ Registry properly allowed with admin")
                test2_passed = True
            else:
                print("    ✗ Registry should be allowed with admin")
                test2_passed = False
                
    except Exception as e:
        print(f"    ✗ Error testing registry with admin: {e}")
        test2_passed = False
    
    return test1_passed and test2_passed

def test_server_error_simulation():
    """Test server error handling"""
    print("\nTesting server error handling...")
    
    # Test with malformed JSON
    print("  Test 1: Malformed JSON...")
    try:
        response = requests.post(
            f"{base_url}/api/system/agent/admin",
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print("    ✓ Malformed JSON properly handled")
            test1_passed = True
        else:
            print("    ✗ Malformed JSON should return 400")
            test1_passed = False
            
    except Exception as e:
        print(f"    ✗ Error testing malformed JSON: {e}")
        test1_passed = False
    
    return test1_passed

def test_boundary_conditions():
    """Test boundary conditions"""
    print("\nTesting boundary conditions...")
    
    # Test with very long agent ID
    print("  Test 1: Very long agent ID...")
    long_agent_id = "a" * 1000
    data = {
        "agent_id": long_agent_id,
        "admin_enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/agent/admin", json=data)
        result = response.json()
        
        if response.status_code == 200:
            print("    ✓ Long agent ID handled correctly")
            test1_passed = True
        else:
            print("    ✗ Long agent ID should be handled")
            test1_passed = False
            
    except Exception as e:
        print(f"    ✗ Error testing long agent ID: {e}")
        test1_passed = False
    
    return test1_passed

def check_server_health():
    """Check if server is responding"""
    try:
        response = requests.get(f"{base_url}/api/agents", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_all_tests():
    """Run all error handling tests"""
    print("🧪 Starting comprehensive error handling validation...\n")
    
    # Check server health first
    print("Checking server health...")
    if not check_server_health():
        print("❌ Server is not responding. Please ensure the server is running.")
        return False
    print("✅ Server is responding\n")
    
    tests = [
        ("Invalid Agent ID Handling", test_invalid_agent_id),
        ("Missing Required Fields", test_missing_required_fields),
        ("Invalid Data Types", test_invalid_data_types),
        ("Admin Privilege Edge Cases", test_admin_privilege_edge_cases),
        ("Server Error Simulation", test_server_error_simulation),
        ("Boundary Conditions", test_boundary_conditions),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            passed = test_func()
            results.append((test_name, passed))
            
            if passed:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("ERROR HANDLING VALIDATION SUMMARY")
    print('='*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<40} {status}")
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All error handling validation tests passed!")
        return True
    else:
        print("⚠️  Some error handling tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)