import os
import schedule
import time
import logging
from datetime import datetime, timedelta
from app.services.price_fetching_service import PostgreSQLOptimizedPriceFetchingService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def daily_eod_update():
    """Run daily after market close (6 PM EST)"""
    
    # Check if API key is available
    api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
    if not api_key:
        logger.error("❌ FINANCIAL_MODELING_PREP_API_KEY not found in environment variables!")
        return
    
    logger.info("🚀 Starting daily EOD price update...")
    logger.info(f"🔑 Using API key: {api_key[:10]}...")
    
    service = PostgreSQLOptimizedPriceFetchingService()
    
    # Get yesterday's date (market data is T+1)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"📅 Updating prices for date range: {yesterday} to {today}")
    
    try:
        # Update all symbols for yesterday only
        service.run_price_collection_single_threaded(
            start_date=yesterday,
            end_date=today,
            max_symbols=None,  # Gets all symbols from StockUniverseService
            symbol_list=None   # Use universe service symbols
        )
        
        logger.info("✅ Daily EOD update complete!")
        
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
        logger.error("❌ No API key found! Set FINANCIAL_MODELING_PREP_API_KEY environment variable")
        exit(1)
    
    # For testing, you can run immediately
    # test_update()  # Uncomment this line to test immediately
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
