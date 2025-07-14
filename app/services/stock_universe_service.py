import requests
import os
from typing import List, Dict
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()

class StockUniverseService:
    def __init__(self):
        self.api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        self.api_url = "https://financialmodelingprep.com/api/v3"
        self.stable_url = "https://financialmodelingprep.com/stable"
    
    def get_historical_sp500_constituents(self) -> List[Dict]:
        """Get ALL historical S&P 500 constituents since 2000"""
        try:
            url = f"{self.stable_url}/historical-sp500-constituent?apikey={self.api_key}"
            print(f"Fetching historical S&P 500 data...")
            response = requests.get(url)
            data = response.json()
            print(f"✅ Found {len(data)} historical S&P 500 records")
            return data
        except Exception as e:
            print(f"❌ Error fetching historical S&P 500: {e}")
            return []
    
    def get_all_etfs(self) -> List[Dict]:
        """Get comprehensive ETF list"""
        try:
            url = f"{self.stable_url}/etf-list?apikey={self.api_key}"
            print(f"Fetching all ETFs...")
            response = requests.get(url)
            data = response.json()
            print(f"✅ Found {len(data)} total ETFs")
            return data
        except Exception as e:
            print(f"❌ Error fetching ETFs: {e}")
            return []
    
    def get_etfs_from_file(self) -> List[str]:
        """Read ETFs from the provided JSON file"""
        print(f"📁 Reading ETFs from etf_tickers.json...")
        
        try:
            # Read the JSON file
            with open('etf_tickers.json', 'r') as f:
                content = f.read()
            
            # Parse the content (format: "VOO, Vanguard S&P 500 ETF")
            etf_list = []
            lines = content.strip().split('\n')
            
            for line in lines:
                if ',' in line:
                    # Extract ticker (everything before first comma)
                    ticker = line.split(',')[0].strip()
                    if ticker:
                        etf_list.append(ticker)
            
            print(f"✅ Found {len(etf_list)} ETFs in file")
            print(f"📊 First 10 ETFs: {etf_list[:10]}")
            return etf_list
            
        except FileNotFoundError:
            print("❌ etf_tickers.json file not found!")
            return []
        except Exception as e:
            print(f"❌ Error reading ETF file: {e}")
            return []
    
    def get_all_symbols_to_track(self) -> List[str]:
        """Get complete list of symbols: S&P 500 + your ETF list"""
        symbols = set()
        
        # Add S&P 500 historical constituents
        sp500_symbols = self.get_unique_sp500_symbols()
        symbols.update(sp500_symbols)
        
        # Add your ETF list
        etf_symbols = self.get_etfs_from_file()
        symbols.update(etf_symbols)
        
        return list(symbols)    
    def get_unique_sp500_symbols(self) -> List[str]:
        """Extract unique stock symbols from historical S&P 500 data"""
        historical_data = self.get_historical_sp500_constituents()
        symbols = set()
        
        for record in historical_data:
            if 'symbol' in record:
                symbols.add(record['symbol'])
        
        unique_symbols = list(symbols)
        print(f"✅ Found {len(unique_symbols)} unique S&P 500 symbols")
        return unique_symbols

if __name__ == "__main__":
    service = StockUniverseService()
    
    print("🚀 Testing Stock Universe with Your ETF File...")
    print("="*60)
    
    # Test 1: Historical S&P 500
    sp500_symbols = service.get_unique_sp500_symbols()
    
    print("\n" + "="*60)
    
    # Test 2: Your ETF list from file
    etf_symbols = service.get_etfs_from_file()
    
    print("\n" + "="*60)
    
    # Test 3: Combined universe
    all_symbols = service.get_all_symbols_to_track()
    print(f"🎯 FINAL STOCK UNIVERSE:")
    print(f"  📈 S&P 500 stocks: {len(sp500_symbols)}")
    print(f"  🏦 ETFs from your list: {len(etf_symbols)}")
    print(f"  🎯 Total unique symbols: {len(all_symbols)}")
    print(f"📈 Complete coverage ready for price fetching!")# Test the service
