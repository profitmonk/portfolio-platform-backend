#!/usr/bin/env python
"""
Test if the app can start up without errors
"""
try:
    print("Testing imports...")
    from app.main import app
    print("✅ FastAPI app imported successfully")
    
    print("Testing database connection...")
    from app.database.connection import engine
    from sqlalchemy import text
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    
    print("Testing auth routes...")
    from app.routes.auth import router
    print("✅ Auth routes imported successfully")
    
    print("Testing portfolio routes...")
    from app.routes.portfolio import router
    print("✅ Portfolio routes imported successfully")
    
    print("🎉 All startup tests passed!")
    
except Exception as e:
    print(f"❌ Startup test failed: {e}")
    import traceback
    traceback.print_exc()
