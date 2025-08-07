#!/usr/bin/env python3
"""Test script to debug messages API endpoint"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"
AUTH_FILE = "auth.json"

def test_messages_api():
    print("Testing Messages API Endpoint")
    print("=" * 50)
    
    # First authenticate
    print("\n1. Authenticating...")
    with open(AUTH_FILE, 'r') as f:
        auth_data = json.load(f)
    
    auth_response = requests.post(f"{BASE_URL}/api/auth", json=auth_data)
    print(f"Auth Status: {auth_response.status_code}")
    print(f"Auth Response: {auth_response.json()}")
    
    if auth_response.status_code != 200:
        print("Authentication failed!")
        return
    
    print("\n2. Testing /api/me...")
    me_response = requests.get(f"{BASE_URL}/api/me")
    print(f"Me Status: {me_response.status_code}")
    print(f"Me Response: {me_response.json()}")
    
    print("\n3. Testing messages endpoint...")
    username = "heyitsmilliexx"
    
    # Test different parameter combinations
    test_cases = [
        ("No params", f"{BASE_URL}/api/user/{username}/messages"),
        ("With limit", f"{BASE_URL}/api/user/{username}/messages?limit=10"),
        ("With offset", f"{BASE_URL}/api/user/{username}/messages?limit=5&offset=0"),
    ]
    
    for test_name, url in test_cases:
        print(f"\n{test_name}: {url}")
        try:
            response = requests.get(url, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Got {data.get('count', 0)} messages")
                if data.get('messages'):
                    print("First message:", json.dumps(data['messages'][0], indent=2))
            else:
                print(f"Error: {response.json()}")
                
        except requests.exceptions.Timeout:
            print("Request timed out!")
        except Exception as e:
            print(f"Exception: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_messages_api()