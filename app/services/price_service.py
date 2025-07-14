import requests
import os
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class PriceService:
    def __init__(self):
        self.api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def get_price_for_date(self, symbol: str, date: str) -> float:
        """Get price for a single stock on a specific date"""
        try:
            # Format: 2023-01-01
            url = f"{self.base_url}/historical-price-full/{symbol}?from={date}&to={date}&apikey={self.api_key}"
            
            response = requests.get(url)
            data = response.json()
            
            if 'historical' in data and len(data['historical']) > 0:
                return data['historical'][0]['close']
            
            return None
            
        except Exception as e:
            print(f"Error getting price for {symbol} on {date}: {e}")
            return None

# Test the service
if __name__ == "__main__":
    service = PriceService()
    price = service.get_price_for_date("AAPL", "2022-01-06")
    print(f"AAPL price on 2023-01-01: ${price}")
