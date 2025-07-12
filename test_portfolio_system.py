import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_portfolio_system():
    """Test complete portfolio management system"""
    print("🔍 Testing portfolio management system...")
    print("-" * 60)
    
    # Test data
    test_user = {
        "email": "portfolio_test@example.com",
        "username": "portfoliotest",
        "password": "testpassword123",
        "display_name": "Portfolio Test User"
    }
    
    try:
        # 1. Register and login
        print("1. Setting up test user...")
        
        # Register
        register_response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
        if register_response.status_code != 201:
            print(f"   Registration failed: {register_response.text}")
            return False
        
        # Login
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        if login_response.status_code != 200:
            print(f"   Login failed: {login_response.text}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ User authenticated successfully")
        
        # 2. Create portfolios
        print("\n2. Creating portfolios...")
        
        portfolios_data = [
            {
                "name": "Tech Growth Test Portfolio",
                "description": "Testing technology investments",
                "is_public": True
            },
            {
                "name": "Private Test Portfolio", 
                "description": "Private portfolio for testing",
                "is_public": False
            }
        ]
        
        created_portfolios = []
        for portfolio_data in portfolios_data:
            response = requests.post(f"{BASE_URL}/api/portfolios/", json=portfolio_data, headers=headers)
            if response.status_code == 201:
                portfolio = response.json()
                created_portfolios.append(portfolio)
                print(f"✅ Created portfolio: {portfolio['name']} (ID: {portfolio['id']})")
            else:
                print(f"❌ Failed to create portfolio: {response.text}")
                return False
        
        # 3. Add holdings
        print("\n3. Adding holdings to portfolio...")
        
        tech_portfolio_id = created_portfolios[0]["id"]
        holdings_data = [
            {
                "symbol": "AAPL",
                "asset_type": "stock",
                "asset_name": "Apple Inc.",
                "quantity": 10.0,
                "average_cost": 150.00
            },
            {
                "symbol": "GOOGL",
                "asset_type": "stock", 
                "asset_name": "Alphabet Inc.",
                "quantity": 5.0,
                "average_cost": 120.00
            },
            {
                "symbol": "MSFT",
                "asset_type": "stock",
                "asset_name": "Microsoft Corporation", 
                "quantity": 8.0,
                "average_cost": 200.00
            }
        ]
        
        created_holdings = []
        for holding_data in holdings_data:
            response = requests.post(
                f"{BASE_URL}/api/portfolios/{tech_portfolio_id}/holdings",
                json=holding_data,
                headers=headers
            )
            if response.status_code == 201:
                holding = response.json()
                created_holdings.append(holding)
                print(f"✅ Added holding: {holding['symbol']} - {holding['quantity']} shares @ ${holding['average_cost']}")
            else:
                print(f"❌ Failed to add holding: {response.text}")
                return False
        
        # 4. Test portfolio calculations
        print("\n4. Testing portfolio calculations...")
        
        response = requests.get(f"{BASE_URL}/api/portfolios/{tech_portfolio_id}", headers=headers)
        if response.status_code == 200:
            portfolio = response.json()
            expected_cost_basis = sum(h['total_cost_basis'] for h in created_holdings)
            
            print(f"✅ Portfolio calculations:")
            print(f"   Total cost basis: ${portfolio['total_cost_basis']:.2f}")
            print(f"   Total value: ${portfolio['total_value']:.2f}")
            print(f"   Holdings count: {portfolio['holdings_count']}")
            print(f"   Expected cost basis: ${expected_cost_basis:.2f}")
            
            if abs(portfolio['total_cost_basis'] - expected_cost_basis) < 0.01:
                print("✅ Portfolio calculations are correct!")
            else:
                print("❌ Portfolio calculations don't match expected values")
                return False
        else:
            print(f"❌ Failed to get portfolio details: {response.text}")
            return False
        
        # 5. Test public portfolio discovery
        print("\n5. Testing public portfolio discovery...")
        
        response = requests.get(f"{BASE_URL}/api/portfolios/public")
        if response.status_code == 200:
            public_portfolios = response.json()
            public_portfolio_names = [p['name'] for p in public_portfolios]
            
            if "Tech Growth Test Portfolio" in public_portfolio_names:
                print("✅ Public portfolio appears in discovery")
            else:
                print("❌ Public portfolio not found in discovery")
                return False
                
            if "Private Test Portfolio" not in public_portfolio_names:
                print("✅ Private portfolio correctly hidden from discovery")
            else:
                print("❌ Private portfolio incorrectly visible in discovery")
                return False
        else:
            print(f"❌ Failed to get public portfolios: {response.text}")
            return False
        
        # 6. Test holdings management
        print("\n6. Testing holdings management...")
        
        # Update a holding
        apple_holding_id = created_holdings[0]["id"]
        update_data = {"quantity": 15.0}
        
        response = requests.put(
            f"{BASE_URL}/api/portfolios/holdings/{apple_holding_id}",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            updated_holding = response.json()
            if updated_holding["quantity"] == 15.0:
                print(f"✅ Updated holding quantity: {updated_holding['symbol']} now has {updated_holding['quantity']} shares")
            else:
                print("❌ Holding update failed")
                return False
        else:
            print(f"❌ Failed to update holding: {response.text}")
            return False
        
        # 7. Test access control
        print("\n7. Testing access control...")
        
        private_portfolio_id = created_portfolios[1]["id"]
        
        # Test without authentication
        response = requests.get(f"{BASE_URL}/api/portfolios/{private_portfolio_id}")
        if response.status_code == 401:
            print("✅ Private portfolio correctly requires authentication")
        else:
            print("❌ Private portfolio should require authentication")
            return False
        
        # Test with authentication
        response = requests.get(f"{BASE_URL}/api/portfolios/{private_portfolio_id}", headers=headers)
        if response.status_code == 200:
            print("✅ Owner can access private portfolio")
        else:
            print("❌ Owner should be able to access private portfolio")
            return False
        
        print("\n" + "-" * 60)
        print("🎉 All portfolio system tests passed!")
        print("✅ Portfolio creation, holdings management, and access control working correctly")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_portfolio_system()
