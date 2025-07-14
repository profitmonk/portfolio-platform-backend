import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def add_adjusted_close_column():
    """Add adjusted_close column to existing asset_prices table"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='asset_prices' AND column_name='adjusted_close'
            """))
            
            if result.fetchone():
                print("✅ adjusted_close column already exists")
                return
            
            # Add the column
            connection.execute(text("""
                ALTER TABLE asset_prices 
                ADD COLUMN adjusted_close FLOAT NOT NULL DEFAULT 0
            """))
            
            connection.commit()
            print("✅ Added adjusted_close column to asset_prices table")
            
    except Exception as e:
        print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_adjusted_close_column()
