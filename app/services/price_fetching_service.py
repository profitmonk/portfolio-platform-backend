import sys
import os
# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text
from sqlalchemy.dialects.postgresql import insert
import time
import logging
from collections import defaultdict

from app.database.connection import get_db
from app.models.asset_price import AssetPrice
from app.services.stock_universe_service import StockUniverseService
from dotenv import load_dotenv

load_dotenv()

# Add logging to see what's taking time
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLOptimizedPriceFetchingService:
    def __init__(self):
        self.api_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
        self.stable_url = "https://financialmodelingprep.com/stable"
        self.universe_service = StockUniverseService()
    
    def get_missing_price_data_fast(self, db: Session, symbols: List[str], start_date: str, end_date: str) -> Dict[str, bool]:
        """Quickly check which symbols need data - PostgreSQL optimized"""
        logger.info(f"🔍 Quick check for missing data...")
        start_time = time.time()
        
        missing_data = {}
        
        # PostgreSQL-compatible query to check all symbols at once
        symbol_counts_query = text("""
            SELECT symbol, COUNT(*) as count 
            FROM asset_prices 
            WHERE symbol = ANY(:symbols) 
            AND date >= :start_date 
            AND date <= :end_date 
            GROUP BY symbol
        """)
        
        symbol_counts = db.execute(
            symbol_counts_query,
            {
                'symbols': symbols,  # PostgreSQL can handle Python lists directly
                'start_date': start_date,
                'end_date': end_date
            }
        ).fetchall()
        
        # Convert to dict
        existing_counts = {row[0]: row[1] for row in symbol_counts}
        
        # If a symbol has less than 4000 records (rough estimate for 20 years), fetch it
        for symbol in symbols:
            count = existing_counts.get(symbol, 0)
            if count < 4000:  # Roughly 20 years of trading days
                missing_data[symbol] = True
                logger.info(f"  📊 {symbol}: has {count} records, needs refresh")
            else:
                logger.info(f"  ✅ {symbol}: has {count} records, looks complete")
        
        elapsed = time.time() - start_time
        logger.info(f"🕒 Missing data check took {elapsed:.2f} seconds")
        return missing_data

    def fetch_historical_prices(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """Your existing fetch method with timing"""
        logger.info(f"📡 Fetching {symbol}...")
        start_time = time.time()
        
        try:
            url = f"{self.stable_url}/historical-price-eod/full?symbol={symbol}&from={start_date}&to={end_date}&apikey={self.api_key}"
            
            response = requests.get(url, timeout=30)  # Add timeout
            data = response.json()
            
            # Handle both response formats
            if isinstance(data, list):
                result = data
            elif isinstance(data, dict) and 'historical' in data:
                result = data['historical']
            else:
                logger.warning(f"  ❌ {symbol}: unexpected response format")
                return []
                
            elapsed = time.time() - start_time
            logger.info(f"  ✅ {symbol}: fetched {len(result)} records in {elapsed:.2f}s")
            return result
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ❌ {symbol}: error after {elapsed:.2f}s - {e}")
            return []

    def store_prices_postgresql_bulk(self, db: Session, symbol: str, price_data: List[Dict]) -> int:
        """PostgreSQL-optimized bulk storage using upsert"""
        if not price_data:
            return 0
            
        logger.info(f"💾 Storing {len(price_data)} records for {symbol}...")
        start_time = time.time()
        
        try:
            # Prepare data for PostgreSQL bulk upsert
            prep_start = time.time()
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
            
            prep_elapsed = time.time() - prep_start
            logger.info(f"  📋 Prepared data in {prep_elapsed:.2f}s")
            
            # Use PostgreSQL's ON CONFLICT for efficient upsert
            bulk_start = time.time()
            
            # Create the insert statement
            stmt = insert(AssetPrice).values(insert_data)
            
            # Handle conflicts by updating the record
            stmt = stmt.on_conflict_do_update(
                index_elements=['symbol', 'date'],
                set_={
                    'open_price': stmt.excluded.open_price,
                    'high_price': stmt.excluded.high_price,
                    'low_price': stmt.excluded.low_price,
                    'close_price': stmt.excluded.close_price,
                    'volume': stmt.excluded.volume,
                    'adjusted_close': stmt.excluded.adjusted_close,
                }
            )
            
            # Execute the bulk upsert
            db.execute(stmt)
            db.commit()
            
            bulk_elapsed = time.time() - bulk_start
            total_elapsed = time.time() - start_time
            
            logger.info(f"  ✅ PostgreSQL upsert completed {len(insert_data)} records in {bulk_elapsed:.2f}s (total: {total_elapsed:.2f}s)")
            
            return len(insert_data)
            
        except Exception as e:
            logger.error(f"  ❌ {symbol}: error storing data - {e}")
            db.rollback()
            
            # Fallback to your existing method
            logger.info(f"  🔄 Falling back to individual inserts for {symbol}")
            return self.store_prices_fallback(db, symbol, price_data)

    def store_prices_fallback(self, db: Session, symbol: str, price_data: List[Dict]) -> int:
        """Fallback to your existing store method"""
        stored_count = 0
        
        for price_record in price_data:
            try:
                # Check if this price already exists
                existing = db.query(AssetPrice).filter(
                    AssetPrice.symbol == symbol,
                    AssetPrice.date == price_record['date']
                ).first()
                
                if not existing:
                    # Get adjusted close from API response
                    adj_close = price_record.get('adjClose', price_record.get('close', 0))
                    
                    asset_price = AssetPrice(
                        symbol=symbol,
                        date=price_record['date'],
                        open_price=price_record.get('open', 0),
                        high_price=price_record.get('high', 0),
                        low_price=price_record.get('low', 0),
                        close_price=price_record.get('close', 0),
                        volume=price_record.get('volume', 0),
                        adjusted_close=adj_close
                    )
                    db.add(asset_price)
                    stored_count += 1
                    
            except Exception as e:
                logger.error(f"    ❌ Error storing {symbol} {price_record.get('date')}: {e}")
                continue
        
        if stored_count > 0:
            try:
                db.commit()
                logger.info(f"  💾 {symbol}: stored {stored_count} new records (fallback method)")
            except Exception as e:
                logger.error(f"  ❌ {symbol}: error committing to database - {e}")
                db.rollback()
                stored_count = 0
        
        return stored_count

    def check_database_performance_postgresql(self, db: Session):
        """PostgreSQL-specific database performance check"""
        logger.info("🔧 Running PostgreSQL database performance check...")
        
        try:
            # Check indexes on asset_prices table
            result = db.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'asset_prices'
                ORDER BY indexname
            """)).fetchall()
            
            logger.info(f"📋 Current indexes on asset_prices: {len(result)}")
            for row in result:
                logger.info(f"  - {row[0]}: {row[1]}")
            
            # Test query performance
            start_time = time.time()
            count = db.execute(text("SELECT COUNT(*) FROM asset_prices")).scalar()
            elapsed = time.time() - start_time
            
            logger.info(f"📊 Total records: {count:,} (query took {elapsed:.3f}s)")
            
            # Check if our key index exists
            key_index_exists = any('idx_symbol_date' in row[0] for row in result)
            if key_index_exists:
                logger.info("✅ Key performance index (idx_symbol_date) found!")
            else:
                logger.warning("⚠️  Key performance index (idx_symbol_date) missing!")
            
        except Exception as e:
            logger.error(f"❌ Error checking database performance: {e}")

    def run_price_collection_fast(self, start_date: str = "2005-01-01", end_date: str = "2024-12-31", max_symbols: int = 3):
        """PostgreSQL-optimized main collection function with detailed timing"""
        logger.info(f"🚀 Starting PostgreSQL-optimized price collection from {start_date} to {end_date}...")
        logger.info(f"📊 Processing first {max_symbols} symbols...")
        
        total_start_time = time.time()
        
        # Get symbols
        all_symbols = self.universe_service.get_all_symbols_to_track()[:max_symbols]
        logger.info(f"🎯 Symbols to process: {all_symbols}")
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Check database performance first
            self.check_database_performance_postgresql(db)
            
            # Quick missing data check
            missing_data = self.get_missing_price_data_fast(db, all_symbols, start_date, end_date)
            
            if not missing_data:
                logger.info("✅ All price data is already up to date!")
                return
            
            logger.info(f"\n🎯 Need to fetch data for {len(missing_data)} symbols")
            
            total_fetched = 0
            total_stored = 0
            
            # Process each symbol
            for symbol in missing_data.keys():
                symbol_start = time.time()
                logger.info(f"\n📈 Processing {symbol}...")
                
                # Fetch data
                fetch_start = time.time()
                price_data = self.fetch_historical_prices(symbol, start_date, end_date)
                fetch_elapsed = time.time() - fetch_start
                
                if price_data:
                    # Store data using PostgreSQL-optimized method
                    store_start = time.time()
                    stored = self.store_prices_postgresql_bulk(db, symbol, price_data)
                    store_elapsed = time.time() - store_start
                    
                    total_fetched += len(price_data)
                    total_stored += stored
                    
                    symbol_elapsed = time.time() - symbol_start
                    logger.info(f"  ⏱️  {symbol} total time: {symbol_elapsed:.2f}s (fetch: {fetch_elapsed:.2f}s, store: {store_elapsed:.2f}s)")
                
                # Small delay to be nice to the API
                time.sleep(0.2)
            
            total_elapsed = time.time() - total_start_time
            
            logger.info(f"\n🎉 PostgreSQL-optimized collection complete!")
            logger.info(f"  ⏱️  Total time: {total_elapsed:.2f} seconds ({total_elapsed/60:.2f} minutes)")
            logger.info(f"  📊 Records fetched: {total_fetched}")
            logger.info(f"  💾 Records stored: {total_stored}")
            if len(missing_data) > 0:
                logger.info(f"  ⚡ Average per symbol: {total_elapsed/len(missing_data):.2f} seconds")
            
        finally:
            db.close()
    def run_price_collection_single_threaded(self, start_date: str = "2005-01-01", end_date: str = "2025-07-13", max_symbols: int = None, symbol_list: List[str] = None):
        """Single-threaded price collection with yearly chunks per symbol"""
        logger.info(f"🚀 Starting SINGLE-THREADED price collection...")
        logger.info(f"📅 Date range: {start_date} to {end_date}")
        
        total_start_time = time.time()
        
        # Get symbols
        # Get symbols - use symbol_list if provided, otherwise get from universe service
        if symbol_list:
            all_symbols = symbol_list
            logger.info(f"🎯 Using provided symbol list: {all_symbols}")
        else:
            all_symbols = self.universe_service.get_all_symbols_to_track()
        if max_symbols:
            all_symbols = all_symbols[:max_symbols]
        
        logger.info(f"🎯 Processing {len(all_symbols)} symbols (single-threaded)")
        
        # Get database session (single connection)
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Quick missing data check
            missing_data = self.get_missing_price_data_fast(db, all_symbols, start_date, end_date)
            
            if not missing_data:
                logger.info("✅ All price data is already up to date!")
                return
            
            logger.info(f"\n🎯 Need to fetch data for {len(missing_data)} symbols")
            
            total_fetched = 0
            total_stored = 0
            
            # Process each symbol ONE AT A TIME
            for i, symbol in enumerate(missing_data.keys()):
                symbol_start = time.time()
                logger.info(f"\n📈 [{i+1}/{len(missing_data)}] Processing {symbol}...")
                
                # Fetch ALL data for this symbol
                price_data = self.fetch_historical_prices(symbol, start_date, end_date)
                
                if price_data:
                    # Store in YEARLY CHUNKS instead of all at once
                    stored = self.store_prices_in_yearly_chunks(db, symbol, price_data)
                    
                    total_fetched += len(price_data)
                    total_stored += stored
                    
                    symbol_elapsed = time.time() - symbol_start
                    logger.info(f"  ⏱️  {symbol} completed in {symbol_elapsed:.2f}s")
                
                # Small delay between symbols
                time.sleep(0.5)
            
            total_elapsed = time.time() - total_start_time
            logger.info(f"\n🎉 Single-threaded collection complete!")
            logger.info(f"  ⏱️  Total time: {total_elapsed:.2f} seconds ({total_elapsed/60:.2f} minutes)")
            logger.info(f"  📊 Records fetched: {total_fetched}")
            logger.info(f"  💾 Records stored: {total_stored}")
            
        finally:
            db.close()
    def store_prices_in_yearly_chunks(self, db: Session, symbol: str, price_data: List[Dict]) -> int:
        """Store with conflict resolution using unique constraint"""
        if not price_data:
            return 0
        
        total_stored = 0
        yearly_data = defaultdict(list)
        
        for record in price_data:
            year = record['date'][:4]
            yearly_data[year].append(record)
        
        for year, year_records in yearly_data.items():
            try:
                insert_data = []
                for record in year_records:
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
                
                # Use ON CONFLICT with the new unique constraint
                stmt = insert(AssetPrice).values(insert_data)
                stmt = stmt.on_conflict_do_update(
                    constraint='uq_asset_prices_symbol_date',  # Use constraint name
                    set_={
                        'open_price': stmt.excluded.open_price,
                        'high_price': stmt.excluded.high_price,
                        'low_price': stmt.excluded.low_price,
                        'close_price': stmt.excluded.close_price,
                        'volume': stmt.excluded.volume,
                        'adjusted_close': stmt.excluded.adjusted_close,
                    }
                )
                
                db.execute(stmt)
                db.commit()
                
                total_stored += len(insert_data)
                logger.info(f"    ✅ {year}: {len(insert_data)} records upserted")
                
            except Exception as e:
                logger.error(f"    ❌ Error storing {symbol} {year}: {e}")
                db.rollback()
                continue
        
        return total_stored    

# Test the PostgreSQL-optimized service
if __name__ == "__main__":
    service = PostgreSQLOptimizedPriceFetchingService()
    
    logger.info("🧪 Testing PostgreSQL-Optimized Price Fetching Service...")
    logger.info("="*80)
    
    # Single-threaded, yearly chunks
    service.run_price_collection_single_threaded(
        start_date="2005-01-01", 
        end_date="2025-07-13",
        max_symbols=None  # All symbols
    )
    #service.run_price_collection_single_threaded(
    #    start_date="2005-01-01", 
    #    end_date="2025-07-13",
    #    symbol_list=["AAPL"]
    #)
    # Run the optimized collection
    #service.run_price_collection_fast(
    #    start_date="2005-01-01", 
    #    end_date="2025-07-13",
    #    max_symbols=None
    #)
