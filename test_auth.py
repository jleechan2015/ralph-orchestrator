#!/usr/bin/env python3
"""Test script for Ralph Orchestrator web authentication."""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_authentication():
    """Test the authentication flow."""
    
    print("Testing Ralph Orchestrator Web Authentication")
    print("=" * 50)
    
    # Test 1: Try to access protected endpoint without auth
    print("\n1. Testing unauthenticated access...")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 401:
            print("✓ Protected endpoint correctly requires authentication")
        else:
            print(f"✗ Expected 401, got {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure it's running on port 8080")
        return
    
    # Test 2: Login with default credentials
    print("\n2. Testing login with default credentials...")
    login_data = {
        "username": "admin",
        "password": "ralph-admin-2024"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=login_data
    )
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print(f"✓ Login successful! Token expires in {token_data['expires_in']} seconds")
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return
    
    # Test 3: Access protected endpoint with token
    print("\n3. Testing authenticated access...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Successfully accessed protected endpoint")
        print(f"  - Status: {data['status']}")
        print(f"  - Active Orchestrators: {data['active_orchestrators']}")
    else:
        print(f"✗ Failed to access protected endpoint: {response.status_code}")
    
    # Test 4: Verify token
    print("\n4. Testing token verification...")
    response = requests.post(f"{BASE_URL}/api/auth/verify", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Token is valid")
        print(f"  - Username: {data['username']}")
        print(f"  - Is Admin: {data['is_admin']}")
    else:
        print(f"✗ Token verification failed: {response.status_code}")
    
    # Test 5: Test with invalid token
    print("\n5. Testing with invalid token...")
    bad_headers = {"Authorization": "Bearer invalid_token_12345"}
    response = requests.get(f"{BASE_URL}/api/status", headers=bad_headers)
    
    if response.status_code == 401:
        print("✓ Invalid token correctly rejected")
    else:
        print(f"✗ Expected 401 for invalid token, got {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Authentication tests completed!")

if __name__ == "__main__":
    test_authentication()