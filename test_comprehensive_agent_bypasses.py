#!/usr/bin/env python3
"""
Test script that mimics frontend API calls for agent-specific bypasses
"""

import requests
import json

def test_frontend_style_api_calls():
    """Test API calls exactly like the frontend would make them"""
    base_url = "http://127.0.0.1:8080"
    
    print("=== Testing Frontend-Style API Calls ===\n")
    
    # Test agent ID from the frontend
    test_agent_id = "frontend-test-agent-001"
    
    # Test methods that would be called from the frontend
    bypass_methods = ["fodhelper", "eventvwr", "computerdefaults"]
    
    print(f"Testing agent: {test_agent_id}")
    print("=" * 50)
    
    for method in bypass_methods:
        print(f"\nTesting {method} bypass:")
        print("-" * 30)
        
        # Test enabling (like toggleAgentBypass in api.ts)
        enable_data = {
            "agent_id": test_agent_id,
            "key": method,
            "enabled": True
        }
        
        try:
            response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=enable_data)
            result = response.json()
            
            print(f"Enable {method}: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
            if response.status_code != 200 or not result.get('success'):
                print(f"  Error: {result.get('error', 'Unknown error')}")
            
            # Test the bypass (like the frontend would)
            test_data = {
                "agent_id": test_agent_id,
                "key": method
            }
            
            response = requests.post(f"{base_url}/api/system/bypasses/test", json=test_data)
            result = response.json()
            
            print(f"Test {method}: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
            if response.status_code == 200 and result.get('success'):
                print(f"  Result: {result.get('result', {})}")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
            
            # Test disabling
            disable_data = {
                "agent_id": test_agent_id,
                "key": method,
                "enabled": False
            }
            
            response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=disable_data)
            result = response.json()
            
            print(f"Disable {method}: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
            if response.status_code != 200 or not result.get('success'):
                print(f"  Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error with {method}: {str(e)}")

def test_multiple_agents_different_settings():
    """Test multiple agents with different bypass settings"""
    base_url = "http://127.0.0.1:8080"
    
    print("\n\n=== Testing Multiple Agents with Different Settings ===\n")
    
    agents_config = {
        "agent-alpha-001": {
            "fodhelper": True,
            "eventvwr": False,
            "computerdefaults": True
        },
        "agent-beta-002": {
            "fodhelper": False,
            "eventvwr": True,
            "computerdefaults": False
        },
        "agent-gamma-003": {
            "fodhelper": True,
            "eventvwr": True,
            "computerdefaults": True
        }
    }
    
    for agent_id, settings in agents_config.items():
        print(f"\nConfiguring agent: {agent_id}")
        print("-" * 40)
        
        for method, enabled in settings.items():
            data = {
                "agent_id": agent_id,
                "key": method,
                "enabled": enabled
            }
            
            try:
                response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=data)
                result = response.json()
                
                status = "ENABLED" if enabled else "DISABLED"
                success = response.status_code == 200 and result.get('success')
                
                print(f"  {method}: {status} {'✓' if success else '✗'}")
                
                if not success:
                    print(f"    Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"  {method}: ERROR - {str(e)}")

if __name__ == "__main__":
    print("Starting comprehensive agent-specific bypasses testing...\n")
    
    test_frontend_style_api_calls()
    test_multiple_agents_different_settings()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)