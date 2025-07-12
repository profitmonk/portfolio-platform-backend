from app.database.connection import SessionLocal, engine
from app.models.user import User
from sqlalchemy import text

def test_user_creation():
    """Test creating a user in the database"""
    db = SessionLocal()
    try:
        # Create a test user
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=User.get_password_hash("testpassword123"),
            display_name="Test User",
            bio="This is a test user for our portfolio platform"
        )
        
        # Add to database
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ User created successfully!")
        print(f"   ID: {test_user.id}")
        print(f"   Email: {test_user.email}")
        print(f"   Username: {test_user.username}")
        print(f"   Display Name: {test_user.display_name}")
        
        # Test password verification
        if User.verify_password("testpassword123", test_user.hashed_password):
            print("✅ Password hashing and verification works!")
        else:
            print("❌ Password verification failed")
            
        # Query the user back
        found_user = db.query(User).filter(User.email == "test@example.com").first()
        if found_user:
            print("✅ Database query works!")
            print(f"   Found user: {found_user.username}")
        else:
            print("❌ Could not query user from database")
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_database_tables():
    """Check what tables exist in the database"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            print("📋 Tables in database:")
            for table in tables:
                print(f"   - {table}")
            
            if 'users' in tables:
                print("✅ Users table exists!")
                return True
            else:
                print("❌ Users table not found")
                return False
                
    except Exception as e:
        print(f"❌ Could not check tables: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing database models...")
    print("-" * 40)
    
    tables_ok = test_database_tables()
    if tables_ok:
        user_test_ok = test_user_creation()
        
        if user_test_ok:
            print("-" * 40)
            print("🎉 All database tests passed!")
            print("✅ Ready to build more models!")
        else:
            print("⚠️  User creation test failed")
    else:
        print("⚠️  Database tables test failed")
