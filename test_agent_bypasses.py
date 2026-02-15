#!/usr/bin/env python3
"""
Test script for agent-specific bypasses functionality
"""

import requests
import json
import time

def test_agent_specific_bypasses():
    """Test bypasses for specific agents"""
    base_url = "http://127.0.0.1:8080"
    
    # Test agent IDs
    test_agents = [
        "agent-001",
        "agent-002", 
        "test-agent-456"
    ]
    
    bypass_methods = [
        "fodhelper",
        "eventvwr", 
        "computerdefaults",
        "sdclt",
        "slui"
    ]
    
    print("=== Testing Agent-Specific Bypasses ===\n")
    
    for agent_id in test_agents:
        print(f"Testing agent: {agent_id}")
        print("-" * 40)
        
        for method in bypass_methods:
            # Test enabling bypass
            enable_data = {
                "agent_id": agent_id,
                "key": method,
                "enabled": True
            }
            
            try:
                response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=enable_data)
                result = response.json()
                
                if response.status_code == 200 and result.get('success'):
                    print(f"  ✓ {method}: ENABLED")
                else:
                    print(f"  ✗ {method}: FAILED - {result.get('error', 'Unknown error')}")
                    
                # Small delay between requests
                time.sleep(0.1)
                
                # Test disabling bypass
                disable_data = {
                    "agent_id": agent_id,
                    "key": method,
                    "enabled": False
                }
                
                response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=disable_data)
                result = response.json()
                
                if response.status_code == 200 and result.get('success'):
                    print(f"  ✓ {method}: DISABLED")
                else:
                    print(f"  ✗ {method}: DISABLE FAILED - {result.get('error', 'Unknown error')}")
                    
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ✗ {method}: ERROR - {str(e)}")
        
        print()
    
    # Test getting current bypass status for agents
    print("=== Testing Bypass Status Retrieval ===\n")
    
    for agent_id in test_agents:
        try:
            # Get current bypass status
            response = requests.get(f"{base_url}/api/system/bypasses")
            result = response.json()
            
            if response.status_code == 200:
                print(f"Agent {agent_id} bypass status:")
                methods = result.get('methods', [])
                agent_methods = [m for m in methods if m.get('agent_id') == agent_id]
                
                if agent_methods:
                    for method in agent_methods:
                        print(f"  - {method['key']}: {'ENABLED' if method['enabled'] else 'DISABLED'}")
                else:
                    print(f"  No bypass methods found for this agent")
            else:
                print(f"  ✗ Failed to get status for {agent_id}")
                
        except Exception as e:
            print(f"  ✗ Error getting status for {agent_id}: {str(e)}")
            
        print()

def test_agent_vs_global_bypasses():
    """Test difference between agent-specific and global bypasses"""
    base_url = "http://127.0.0.1:8080"
    
    print("=== Testing Agent vs Global Bypasses ===\n")
    
    # Test global bypass
    print("Testing global bypass (no agent_id):")
    global_data = {
        "key": "fodhelper",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=global_data)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print("  ✓ Global fodhelper bypass: ENABLED")
        else:
            print(f"  ✗ Global fodhelper bypass: FAILED - {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"  ✗ Global bypass error: {str(e)}")
    
    # Test agent-specific bypass
    print("\nTesting agent-specific bypass:")
    agent_data = {
        "agent_id": "agent-specific-001",
        "key": "fodhelper",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=agent_data)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print("  ✓ Agent-specific fodhelper bypass: ENABLED")
        else:
            print(f"  ✗ Agent-specific fodhelper bypass: FAILED - {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"  ✗ Agent-specific bypass error: {str(e)}")

if __name__ == "__main__":
    print("Starting agent-specific bypasses testing...\n")
    
    test_agent_specific_bypasses()
    test_agent_vs_global_bypasses()
    
    print("\n=== Test Complete ===")