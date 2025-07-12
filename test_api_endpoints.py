import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/auth/login"
PORTFOLIO_URL = f"{BASE_URL}/api/portfolios"  # Changed from /portfolios to /api/portfolios

def test_snapshot_api():
    # Step 1: Login to get token
    login_data = {
        "email": "testoggn1@example.com",  # Use your test user email
        "password": "testoggn1"
    }
    
    login_response = requests.post(LOGIN_URL, json=login_data)
    if login_response.status_code != 200:
        print("❌ Login failed:", login_response.text)
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful")
    
    # Step 2: Create a test portfolio
    portfolio_data = {
        "name": "Test Snapshot Portfolio",
        "description": "Testing snapshot functionality",
        "is_public": False
    }
    
    portfolio_response = requests.post(PORTFOLIO_URL + "/", json=portfolio_data, headers=headers)
    if portfolio_response.status_code != 201:
        print("❌ Portfolio creation failed:", portfolio_response.text)
        return
    
    portfolio_id = portfolio_response.json()["id"]
    print(f"✅ Portfolio created with ID: {portfolio_id}")
    
    # Step 3: Create a snapshot
    snapshot_data = {
        "snapshot_date": "2024-01-01T00:00:00",
        "assets": "AAPL,MSFT,TSLA",
        "weights": "50,30,20",
        "notes": "Initial allocation"
    }
    
    # Note: snapshot endpoints are at /portfolios/{id}/snapshots (no /api prefix)
    snapshot_response = requests.post(
        f"{BASE_URL}/portfolios/{portfolio_id}/snapshots", 
        json=snapshot_data, 
        headers=headers
    )
    
    if snapshot_response.status_code != 200:
        print("❌ Snapshot creation failed:", snapshot_response.text)
        return
    
    snapshot = snapshot_response.json()
    print(f"✅ Snapshot created:")
    print(f"   Assets: {snapshot['asset_list']}")
    print(f"   Weights: {snapshot['weight_list']}")
    print(f"   Allocation: {snapshot['allocation_dict']}")
    
    # Step 4: Get all snapshots
    get_response = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/snapshots", headers=headers)
    if get_response.status_code != 200:
        print("❌ Get snapshots failed:", get_response.text)
        return
    
    snapshots = get_response.json()
    print(f"✅ Retrieved {len(snapshots)} snapshots")
    
    # Step 5: Create another snapshot (rebalancing)
    snapshot_data_2 = {
        "snapshot_date": "2024-02-01T00:00:00",
        "assets": "AAPL,QQQ,CASH",
        "weights": "40,40,20",
        "notes": "Rebalanced to include QQQ"
    }
    
    snapshot_response_2 = requests.post(
        f"{BASE_URL}/portfolios/{portfolio_id}/snapshots", 
        json=snapshot_data_2, 
        headers=headers
    )
    
    if snapshot_response_2.status_code == 200:
        print("✅ Second snapshot (rebalancing) created successfully")
    else:
        print("❌ Second snapshot failed:", snapshot_response_2.text)
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_snapshot_api()
