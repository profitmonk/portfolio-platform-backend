import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_authentication_flow():
    """Test complete authentication flow"""
    print("🔍 Testing authentication system...")
    print("-" * 50)
    
    # Test data
    test_user = {
        "email": "automation_test@example.com",
        "username": "autotest",
        "password": "testpassword123",
        "display_name": "Automation Test User"
    }
    
    try:
        # 1. Test user registration
        print("1. Testing user registration...")
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user
        )
        
        if register_response.status_code == 201:
            user_data = register_response.json()
            print(f"✅ User registered: {user_data['username']}")
            print(f"   ID: {user_data['id']}")
            print(f"   Email: {user_data['email']}")
        else:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"   Error: {register_response.text}")
            return False
        
        # 2. Test user login
        print("\n2. Testing user login...")
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data["access_token"]
            print(f"✅ Login successful")
            print(f"   Token type: {token_data['token_type']}")
            print(f"   Expires in: {token_data['expires_in']} seconds")
            print(f"   Token preview: {access_token[:50]}...")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Error: {login_response.text}")
            return False
        
        # 3. Test protected endpoint
        print("\n3. Testing protected endpoint...")
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        
        if me_response.status_code == 200:
            user_info = me_response.json()
            print(f"✅ Protected endpoint works")
            print(f"   Current user: {user_info['username']}")
            print(f"   Email: {user_info['email']}")
            print(f"   Active: {user_info['is_active']}")
        else:
            print(f"❌ Protected endpoint failed: {me_response.status_code}")
            print(f"   Error: {me_response.text}")
            return False
        
        # 4. Test invalid token
        print("\n4. Testing invalid token...")
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        invalid_response = requests.get(f"{BASE_URL}/auth/me", headers=invalid_headers)
        
        if invalid_response.status_code == 401:
            print("✅ Invalid token properly rejected")
        else:
            print(f"❌ Invalid token should be rejected but got: {invalid_response.status_code}")
        
        # 5. Test duplicate registration
        print("\n5. Testing duplicate registration...")
        duplicate_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user
        )
        
        if duplicate_response.status_code == 400:
            print("✅ Duplicate registration properly rejected")
        else:
            print(f"❌ Duplicate registration should fail but got: {duplicate_response.status_code}")
        
        print("\n" + "-" * 50)
        print("🎉 All authentication tests passed!")
        print("✅ Registration, login, and JWT protection working correctly")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_authentication_flow()
