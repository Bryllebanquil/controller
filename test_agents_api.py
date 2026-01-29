import requests

def test_agents_api():
    base_url = "http://127.0.0.1:8080"
    
    try:
        # Test getting agents list
        response = requests.get(f"{base_url}/api/agents")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Response length: {len(response.text)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Agents found: {len(data.get('agents', []))}")
                for agent in data.get('agents', [])[:3]:  # Show first 3 agents
                    print(f"  - {agent.get('name', 'Unknown')}: is_admin={agent.get('is_admin', 'missing')}")
            except Exception as e:
                print(f"JSON parse error: {e}")
                print(f"First 200 chars: {response.text[:200]}")
        else:
            print(f"Error response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_agents_api()