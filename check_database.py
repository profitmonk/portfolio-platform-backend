#!/usr/bin/env python
"""
Check if database connection works
"""
import os
from dotenv import load_dotenv

load_dotenv()

def check_database():
    """Test database connection"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL environment variable not found")
            return False
        
        # Don't print the actual URL for security
        print("🔍 DATABASE_URL environment variable found")
        
        from sqlalchemy import create_engine, text
        
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    check_database()
