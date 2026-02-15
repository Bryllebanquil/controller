#!/usr/bin/env python3
"""
Test script specifically for fodhelper bypass functionality
"""

import requests
import json

def test_fodhelper_bypass():
    """Test fodhelper bypass for specific agents"""
    base_url = "http://127.0.0.1:8080"
    
    print("=== Testing Fodhelper Bypass for Specific Agents ===\n")
    
    # Test agents
    agents = ["agent-test-001", "agent-specific-123", "fodhelper-test-agent"]
    
    for agent_id in agents:
        print(f"Testing fodhelper for agent: {agent_id}")
        print("-" * 50)
        
        # Test enabling fodhelper
        enable_data = {
            "agent_id": agent_id,
            "key": "fodhelper",
            "enabled": True
        }
        
        try:
            response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=enable_data)
            result = response.json()
            
            print(f"Enable fodhelper: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
            if response.status_code != 200 or not result.get('success'):
                print(f"  Error: {result.get('error', 'Unknown error')}")
            
            # Test the fodhelper
            test_data = {
                "agent_id": agent_id,
                "key": "fodhelper"
            }
            
            response = requests.post(f"{base_url}/api/system/bypasses/test", json=test_data)
            result = response.json()
            
            print(f"Test fodhelper: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
            if response.status_code == 200 and result.get('success'):
                print(f"  Test result: {result.get('result', 'No result')}")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
            
            # Test disabling fodhelper
            disable_data = {
                "agent_id": agent_id,
                "key": "fodhelper",
                "enabled": False
            }
            
            response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=disable_data)
            result = response.json()
            
            print(f"Disable fodhelper: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
            if response.status_code != 200 or not result.get('success'):
                print(f"  Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print()

def test_fodhelper_global_vs_agent():
    """Test difference between global and agent-specific fodhelper"""
    base_url = "http://127.0.0.1:8080"
    
    print("=== Testing Global vs Agent-Specific Fodhelper ===\n")
    
    # Test global fodhelper
    print("Testing GLOBAL fodhelper bypass:")
    global_data = {
        "key": "fodhelper",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=global_data)
        result = response.json()
        
        print(f"Global enable: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
        
        # Test global fodhelper
        test_response = requests.post(f"{base_url}/api/system/bypasses/test", json={"key": "fodhelper"})
        test_result = test_response.json()
        print(f"Global test: {'✓ SUCCESS' if test_response.status_code == 200 and test_result.get('success') else '✗ FAILED'}")
        
    except Exception as e:
        print(f"Global error: {str(e)}")
    
    print()
    
    # Test agent-specific fodhelper
    print("Testing AGENT-SPECIFIC fodhelper bypass:")
    agent_data = {
        "agent_id": "specific-fodhelper-agent",
        "key": "fodhelper",
        "enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/system/bypasses/toggle", json=agent_data)
        result = response.json()
        
        print(f"Agent-specific enable: {'✓ SUCCESS' if response.status_code == 200 and result.get('success') else '✗ FAILED'}")
        
        # Test agent-specific fodhelper
        test_data = {
            "agent_id": "specific-fodhelper-agent",
            "key": "fodhelper"
        }
        test_response = requests.post(f"{base_url}/api/system/bypasses/test", json=test_data)
        test_result = test_response.json()
        print(f"Agent-specific test: {'✓ SUCCESS' if test_response.status_code == 200 and test_result.get('success') else '✗ FAILED'}")
        
    except Exception as e:
        print(f"Agent-specific error: {str(e)}")

if __name__ == "__main__":
    print("Starting fodhelper bypass testing...\n")
    
    test_fodhelper_bypass()
    test_fodhelper_global_vs_agent()
    
    print("\n=== Fodhelper Test Complete ===")