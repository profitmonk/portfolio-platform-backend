import requests

# Replace with your actual API key
API_KEY = "htcefjICyIMAJrbHaE96woNOE4VmUs5x"

# Test getting Apple's price for a specific date
url = f"https://financialmodelingprep.com/api/v3/historical-price-full/AAPL?from=2022-01-01&to=2023-01-02&apikey={API_KEY}"

response = requests.get(url)
print("Status:", response.status_code)
print("Data:", response.json())
