#!/usr/bin/env python3
"""
Test script for admin privilege indicator functionality
"""

import requests
import json

def test_admin_privilege_indicator():
    """Test the admin privilege indicator functionality"""
    base_url = "http://127.0.0.1:8080"
    
    print("=== Testing Admin Privilege Indicator ===\n")
    
    # Test agents
    test_agents = ["admin-agent-001", "user-agent-002", "admin-agent-003"]
    
    # Set admin status for agents
    for i, agent_id in enumerate(test_agents):
        admin_status = i % 2 == 0  # First and third agents are admin
        
        print(f"Setting admin status for {agent_id}: {'Admin' if admin_status else 'User'}")
        
        data = {
            "agent_id": agent_id,
            "admin_enabled": admin_status
        }
        
        try:
            response = requests.post(f"{base_url}/api/system/agent/admin", json=data)
            result = response.json()
            
            if response.status_code == 200 and result.get('success'):
                print(f"  ✓ Admin status set successfully")
            else:
                print(f"  ✗ Failed to set admin status: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ✗ Error setting admin status: {str(e)}")
    
    print("\n" + "="*50)
    
    # Test getting agents list with admin status
    print("\nTesting agents list with admin status:")
    
    try:
        response = requests.get(f"{base_url}/api/agents")
        result = response.json()
        
        if response.status_code == 200:
            agents = result.get('agents', [])
            print(f"Found {len(agents)} agents:")
            
            for agent in agents:
                agent_name = agent.get('name', 'Unknown')
                is_admin = agent.get('is_admin', False)
                status = agent.get('status', 'unknown')
                
                admin_indicator = "🛡️ Admin" if is_admin else "👤 User"
                status_indicator = "🟢 Online" if status == 'online' else "🔴 Offline"
                
                print(f"  {agent_name}: {admin_indicator} | {status_indicator}")
                
        else:
            print(f"  ✗ Failed to get agents list: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"  ✗ Error getting agents list: {str(e)}")
    
    print("\n" + "="*50)
    
    # Test individual agent details
    print("\nTesting individual agent details:")
    
    for agent_id in test_agents:
        try:
            response = requests.get(f"{base_url}/api/agents/{agent_id}")
            result = response.json()
            
            if response.status_code == 200:
                agent_name = result.get('name', 'Unknown')
                is_admin = result.get('is_admin', False)
                status = result.get('status', 'unknown')
                
                admin_indicator = "🛡️ Admin" if is_admin else "👤 User"
                status_indicator = "🟢 Online" if status == 'online' else "🔴 Offline"
                
                print(f"  {agent_name}: {admin_indicator} | {status_indicator}")
            else:
                print(f"  ✗ Failed to get {agent_id}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ✗ Error getting {agent_id}: {str(e)}")

if __name__ == "__main__":
    test_admin_privilege_indicator()