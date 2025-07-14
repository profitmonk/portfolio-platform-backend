import requests
import os

API_KEY = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
url = f"https://financialmodelingprep.com/api/v3/etf?apikey={API_KEY}"

print("🔍 Debugging ETF API...")
print(f"URL: {url}")

response = requests.get(url)
print(f"Status Code: {response.status_code}")
print(f"Response Type: {type(response.json())}")

data = response.json()
print(f"Data: {data}")

if isinstance(data, list):
    print(f"✅ It's a list with {len(data)} items")
    if len(data) > 0:
        print(f"First item: {data[0]}")
elif isinstance(data, dict):
    print(f"⚠️ It's a dict with keys: {data.keys()}")
else:
    print(f"❌ Unexpected data type: {type(data)}")
