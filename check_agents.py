#!/usr/bin/env python3

import requests
import json

def check_agents():
    """Check if agents are visible in the frontend"""
    try:
        # Try to get agents list from the server
        response = requests.get("https://agent-controller-backend.onrender.com/api/agents", timeout=10)
        if response.status_code == 200:
            agents = response.json()
            print(f"✓ Found {len(agents)} agents:")
            for agent in agents:
                print(f"  - {agent}")
        else:
            print(f"✗ API returned status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error checking agents: {e}")
    
    # Also try the main page
    try:
        response = requests.get("https://agent-controller-backend.onrender.com/", timeout=10)
        print(f"✓ Frontend accessible: {response.status_code}")
        if "agent" in response.text.lower():
            print("✓ Frontend contains agent-related content")
        else:
            print("⚠ Frontend may not show agents")
    except Exception as e:
        print(f"✗ Error accessing frontend: {e}")

if __name__ == "__main__":
    check_agents()