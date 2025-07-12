import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test connection to Railway PostgreSQL database"""
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in .env file")
            return False
        
        print(f"🔍 Connecting to database...")
        print(f"   Host: {database_url.split('@')[1].split(':')[0]}")
        
        # Create engine and test connection
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                print("✅ Database connection successful!")
                print("✅ Railway PostgreSQL is accessible")
                return True
            else:
                print("❌ Database query failed")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
