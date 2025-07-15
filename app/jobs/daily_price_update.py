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
    """Simplified daily update service with duplicate protection"""
    
    def store_prices_simple_bulk(self, db, symbol: str, price_data: list) -> int:
        """Simple bulk insert with duplicate checking"""
        if not price_data:
            return 0
        
        logger.info(f"💾 Checking and storing {len(price_data)} records for {symbol}...")
        
        try:
            new_records = []
            for record in price_data:
                # Check if this record already exists
                existing = db.query(AssetPrice).filter(
                    AssetPrice.symbol == symbol,
                    AssetPrice.date == record['date']
                ).first()
                
                if not existing:
                    adj_close = record.get('adjClose', record.get('close', 0))
                    new_records.append({
                        'symbol': symbol,
                        'date': record['date'],
                        'open_price': record.get('open', 0),
                        'high_price': record.get('high', 0),
                        'low_price': record.get('low', 0),
                        'close_price': record.get('close', 0),
                        'volume': record.get('volume', 0),
                        'adjusted_close': adj_close
                    })
            
            if new_records:
                # Only insert truly new records
                db.bulk_insert_mappings(AssetPrice, new_records)
                db.commit()
                logger.info(f"  ✅ {symbol}: stored {len(new_records)} new records")
                return len(new_records)
            else:
                logger.info(f"  📋 {symbol}: no new records to store")
                return 0
                
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
        
        # Check if it's a weekend (no market data expected)
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        if date_obj.weekday() >= 5:  # Saturday = 5, Sunday = 6
            logger.info(f"📅 {target_date} is a weekend - no market data expected")
            return
        
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
                        # Store using duplicate-protected bulk insert
                        stored = self.store_prices_simple_bulk(db, symbol, price_data)
                        total_fetched += len(price_data)
                        total_stored += stored
                        success_count += 1
                    else:
                        logger.debug(f"  📭 No data for {symbol} on {target_date}")
                    
                    # Delay to be nice to API
                    time.sleep(0.5)  # Increased from 0.1 to avoid rate limits
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to process {symbol}: {e}")
                    error_count += 1
                    continue
            
            logger.info(f"\n🎉 Daily update complete for {target_date}!")
            logger.info(f"  🎯 Total symbols attempted: {len(all_symbols)}")
            logger.info(f"  ✅ Successful updates: {success_count}")
            logger.info(f"  ❌ Failed updates: {error_count}")
            logger.info(f"  📈 Success rate: {(success_count/len(all_symbols)*100):.1f}%")
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

def test_update_specific_date(target_date: str):
    """Test function for specific date"""
    logger.info(f"🧪 Running test update for {target_date}...")
    service = DailyPriceUpdateService()
    service.run_daily_update(target_date)

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
    
    # For testing - run immediately (duplicate protection prevents duplicates)
    logger.info("🧪 Running test update for today...")
    test_update()
    test_update_specific_date("2025-07-12")
    
    # Then start scheduler for future runs
    logger.info("🔄 Starting scheduler for future runs...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
        
        # Heartbeat every hour
        if int(time.time()) % 3600 == 0:
            logger.info("💓 Worker service heartbeat - still running...")
