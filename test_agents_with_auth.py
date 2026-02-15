import requests

def test_agents_with_auth():
    base_url = "http://127.0.0.1:8080"
    
    # First, let's try to login
    login_data = {
        "username": "admin",
        "password": "testpassword123"
    }
    
    print("Attempting to login...")
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"Login result: {login_result}")
            
            # Now try to get agents with session
            session = requests.Session()
            session.cookies.update(login_response.cookies)
            
            print("\nGetting agents with authenticated session...")
            agents_response = session.get(f"{base_url}/api/agents")
            print(f"Agents status: {agents_response.status_code}")
            print(f"Content-Type: {agents_response.headers.get('content-type', 'unknown')}")
            
            if agents_response.status_code == 200:
                try:
                    agents_data = agents_response.json()
                    print(f"Found {len(agents_data.get('agents', []))} agents")
                    for agent in agents_data.get('agents', [])[:2]:
                        print(f"  - {agent.get('name', 'Unknown')}: is_admin={agent.get('is_admin', 'missing')}")
                except Exception as e:
                    print(f"JSON parse error: {e}")
                    print(f"Response: {agents_response.text[:200]}")
            else:
                print(f"Error: {agents_response.text[:200]}")
        else:
            print(f"Login failed: {login_response.text[:200]}")
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_agents_with_auth()