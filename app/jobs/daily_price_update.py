# app/jobs/daily_price_update.py
import sys
import os
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import schedule
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from app.services.price_fetching_service import PostgreSQLOptimizedPriceFetchingService
from app.database.connection import get_db
from app.models.asset_price import AssetPrice
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DailyPriceUpdateService(PostgreSQLOptimizedPriceFetchingService):
    """Simplified daily update service without conflict resolution"""
    
    def store_prices_simple_bulk(self, db, symbol: str, price_data: list) -> int:
        """Simple bulk insert for daily updates - no conflict resolution needed"""
        if not price_data:
            return 0
        
        logger.info(f"💾 Storing {len(price_data)} records for {symbol}...")
        
        try:
            insert_data = []
            for record in price_data:
                adj_close = record.get('adjClose', record.get('close', 0))
                insert_data.append({
                    'symbol': symbol,
                    'date': record['date'],
                    'open_price': record.get('open', 0),
                    'high_price': record.get('high', 0),
                    'low_price': record.get('low', 0),
                    'close_price': record.get('close', 0),
                    'volume': record.get('volume', 0),
                    'adjusted_close': adj_close
                })
            
            # Simple bulk insert
            db.bulk_insert_mappings(AssetPrice, insert_data)
            db.commit()
            
            logger.info(f"  ✅ {symbol}: stored {len(insert_data)} records")
            return len(insert_data)
            
        except Exception as e:
            logger.error(f"  ❌ Error storing {symbol}: {e}")
            db.rollback()
            return 0
    
    def run_daily_update(self, target_date: str = None):
        """Run daily price update for a specific date"""
        if not target_date:
            # Default to yesterday (market data is T+1)
            target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        logger.info(f"🚀 Starting daily price update for {target_date}")
        
        # Get all symbols from universe service
        all_symbols = self.universe_service.get_all_symbols_to_track()
        logger.info(f"🎯 Processing {len(all_symbols)} symbols")
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            total_fetched = 0
            total_stored = 0
            success_count = 0
            error_count = 0
            
            for i, symbol in enumerate(all_symbols):
                try:
                    logger.info(f"📈 [{i+1}/{len(all_symbols)}] Processing {symbol} for {target_date}")
                    
                    # Fetch data for just this date
                    price_data = self.fetch_historical_prices(symbol, target_date, target_date)
                    
                    if price_data:
                        # Store using simple bulk insert
                        stored = self.store_prices_simple_bulk(db, symbol, price_data)
                        total_fetched += len(price_data)
                        total_stored += stored
                        success_count += 1
                    else:
                        logger.warning(f"  ⚠️  No data found for {symbol} on {target_date}")
                    
                    # Small delay to be nice to API
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to process {symbol}: {e}")
                    error_count += 1
                    continue
            
            logger.info(f"\n🎉 Daily update complete for {target_date}!")
            logger.info(f"  ✅ Successful: {success_count} symbols")
            logger.info(f"  ❌ Errors: {error_count} symbols") 
            logger.info(f"  📊 Records fetched: {total_fetched}")
            logger.info(f"  💾 Records stored: {total_stored}")
            
        finally:
            db.close()

def daily_eod_update():
    """Main function called by scheduler"""
    
    # Check if API key is available
    api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
    if not api_key:
        logger.error("❌ FINANCIAL_MODELING_PREP_API_KEY not found!")
        return
    
    logger.info(f"🔑 Using API key: {api_key[:10]}...")
    
    try:
        service = DailyPriceUpdateService()
        service.run_daily_update()
        logger.info("✅ Daily EOD update completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Daily update failed: {e}")
        raise

def test_update():
    """Test function for manual testing"""
    logger.info("🧪 Running test update...")
    daily_eod_update()

# Schedule for 6:30 PM EST (after markets close) - weekdays only
schedule.every().monday.at("18:30").do(daily_eod_update)
schedule.every().tuesday.at("18:30").do(daily_eod_update)
schedule.every().wednesday.at("18:30").do(daily_eod_update)
schedule.every().thursday.at("18:30").do(daily_eod_update)
schedule.every().friday.at("18:30").do(daily_eod_update)

if __name__ == "__main__":
    logger.info("📅 Daily price update scheduler started...")
    logger.info("⏰ Scheduled for 6:30 PM EST, Monday-Friday")
    
    # Check API key on startup
    api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
    if api_key:
        logger.info(f"🔑 API key loaded: {api_key[:10]}...")
    else:
        logger.error("❌ No API key found!")
        exit(1)
    
    # For testing, uncomment this line to run immediately:
    test_update()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
