import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
print(f"🔍 API Key: {API_KEY[:10]}...{API_KEY[-10:] if API_KEY else 'None'}")

# Test 1: Simple stock price call (should work)
print("\n🧪 Test 1: Simple AAPL price...")
url1 = f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={API_KEY}"
response1 = requests.get(url1)
print(f"Status: {response1.status_code}")
print(f"Data: {response1.json()}")

# Test 2: Current S&P 500 (simpler than historical)
print("\n🧪 Test 2: Current S&P 500...")
url2 = f"https://financialmodelingprep.com/api/v3/sp500_constituent?apikey={API_KEY}"
response2 = requests.get(url2)
print(f"Status: {response2.status_code}")
print(f"Data type: {type(response2.json())}")
data2 = response2.json()
if isinstance(data2, list):
    print(f"Found {len(data2)} items")
    if len(data2) > 0:
        print(f"First item: {data2[0]}")
else:
    print(f"Data: {data2}")

# Test 3: Historical S&P 500
print("\n🧪 Test 3: Historical S&P 500...")
url3 = f"https://financialmodelingprep.com/api/v3/historical-sp500-constituent?apikey={API_KEY}"
response3 = requests.get(url3)
print(f"Status: {response3.status_code}")
print(f"Data type: {type(response3.json())}")
data3 = response3.json()
if isinstance(data3, list):
    print(f"Found {len(data3)} items")
    if len(data3) > 0:
        print(f"First item: {data3[0]}")
else:
    print(f"Data: {data3}")

# Test 4: ETF list
print("\n🧪 Test 4: ETF list...")
url4 = f"https://financialmodelingprep.com/api/v3/etf?apikey={API_KEY}"
response4 = requests.get(url4)
print(f"Status: {response4.status_code}")
print(f"Data type: {type(response4.json())}")
data4 = response4.json()
if isinstance(data4, list):
    print(f"Found {len(data4)} items")
    if len(data4) > 0:
        print(f"First item: {data4[0]}")
else:
    print(f"Data: {data4}")
