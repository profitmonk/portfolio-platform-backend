import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def check_tables():
    """Check what tables exist in the database"""
    try:
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print("📋 Tables in database:")
            for table in tables:
                print(f"   - {table}")
            
            expected_tables = ['users', 'portfolios', 'holdings', 'historical_performance', 'follows']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"\n❌ Missing tables: {missing_tables}")
                print("Need to run migrations!")
                return False
            else:
                print("\n✅ All expected tables exist!")
                return True
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    check_tables()
