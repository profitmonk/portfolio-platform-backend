import requests

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/auth/login"
PORTFOLIO_URL = f"{BASE_URL}/api/portfolios"

def test_csv_upload():
    # Step 1: Login
    login_data = {
        "email": "testoggn1@example.com",
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
        "name": "CSV Test Portfolio",
        "description": "Testing CSV upload functionality",
        "is_public": False
    }
    
    portfolio_response = requests.post(PORTFOLIO_URL + "/", json=portfolio_data, headers=headers)
    if portfolio_response.status_code != 201:
        print("❌ Portfolio creation failed:", portfolio_response.text)
        return
    
    portfolio_id = portfolio_response.json()["id"]
    print(f"✅ Portfolio created with ID: {portfolio_id}")
    
    # Step 3: Upload CSV file
    csv_file_path = "history_compact_monthly.csv"  # Update this path if needed
    
    try:
        with open(csv_file_path, 'rb') as csv_file:
            files = {'file': (csv_file_path, csv_file, 'text/csv')}
            
            upload_response = requests.post(
                f"{BASE_URL}/portfolios/{portfolio_id}/snapshots/upload-csv",
                files=files,
                headers=headers
            )
            
            print(f"📤 CSV upload status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                print(f"✅ CSV upload successful!")
                print(f"   Snapshots created: {result['snapshots_created']}")
                print(f"   Errors: {result['errors']}")
            else:
                print(f"❌ CSV upload failed: {upload_response.text}")
    
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file_path}")
        print("   Please make sure the CSV file is in the current directory")
    
    # Step 4: Verify snapshots were created
    snapshots_response = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/snapshots", headers=headers)
    if snapshots_response.status_code == 200:
        snapshots = snapshots_response.json()
        print(f"✅ Portfolio now has {len(snapshots)} snapshots")
        
        # Show first few snapshots
        for i, snapshot in enumerate(snapshots[:3]):
            print(f"   Snapshot {i+1}: {snapshot['snapshot_date'][:10]} - {snapshot['allocation_dict']}")
    
    print("\n🎉 CSV upload test completed!")

if __name__ == "__main__":
    test_csv_upload()
