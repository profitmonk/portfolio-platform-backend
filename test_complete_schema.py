from app.database.connection import SessionLocal, engine
from app.models import User, Portfolio, Holding, AssetType, HistoricalPerformance, Follow
from sqlalchemy import text
from datetime import datetime, date

def test_complete_schema():
    """Test all database models and relationships"""
    db = SessionLocal()
    try:
        print("🔍 Testing complete database schema...")
        
        # 1. Create a test user
        user = User(
            email="portfolio_user@example.com",
            username="portfoliouser",
            hashed_password=User.get_password_hash("secure123"),
            display_name="Portfolio User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User created: {user.username} (ID: {user.id})")
        
        # 2. Create a test portfolio
        portfolio = Portfolio(
            user_id=user.id,
            name="My Test Portfolio",
            description="A portfolio for testing our platform",
            is_public=True,
            total_value=10000.0,
            total_cost_basis=8500.0
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        print(f"✅ Portfolio created: {portfolio.name} (ID: {portfolio.id})")
        
        # 3. Create test holdings
        holdings_data = [
            {
                "symbol": "AAPL",
                "asset_type": AssetType.STOCK,
                "asset_name": "Apple Inc.",
                "quantity": 10.0,
                "average_cost": 150.0,
                "current_price": 155.0
            },
            {
                "symbol": "GOOGL",
                "asset_type": AssetType.STOCK,
                "asset_name": "Alphabet Inc.",
                "quantity": 5.0,
                "average_cost": 120.0,
                "current_price": 125.0
            }
        ]
        
        for holding_data in holdings_data:
            holding = Holding(
                portfolio_id=portfolio.id,
                symbol=holding_data["symbol"],
                asset_type=holding_data["asset_type"],
                asset_name=holding_data["asset_name"],
                quantity=holding_data["quantity"],
                average_cost=holding_data["average_cost"],
                current_price=holding_data["current_price"],
                purchase_date=datetime.now()
            )
            holding.calculate_values()
            db.add(holding)
            
        db.commit()
        print(f"✅ Holdings created: {len(holdings_data)} stocks added")
        
        # 4. Create historical performance record
        performance = HistoricalPerformance(
            portfolio_id=portfolio.id,
            date=date.today(),
            total_value=portfolio.total_value,
            total_cost_basis=portfolio.total_cost_basis,
            total_return_amount=portfolio.total_value - portfolio.total_cost_basis,
            total_return_percentage=((portfolio.total_value - portfolio.total_cost_basis) / portfolio.total_cost_basis) * 100
        )
        db.add(performance)
        db.commit()
        print(f"✅ Historical performance record created")
        
        # 5. Test queries
        # Query user's portfolios
        user_portfolios = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        print(f"✅ Query test: User has {len(user_portfolios)} portfolio(s)")
        
        # Query portfolio holdings
        portfolio_holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        print(f"✅ Query test: Portfolio has {len(portfolio_holdings)} holding(s)")
        
        # Query historical performance
        performance_records = db.query(HistoricalPerformance).filter(HistoricalPerformance.portfolio_id == portfolio.id).all()
        print(f"✅ Query test: Portfolio has {len(performance_records)} performance record(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def check_all_tables():
    """Check what tables exist in the database"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print("📋 All tables in database:")
            for table in tables:
                print(f"   - {table}")
            
            expected_tables = ['users', 'portfolios', 'holdings', 'historical_performance', 'follows']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            else:
                print("✅ All expected tables exist!")
                return True
                
    except Exception as e:
        print(f"❌ Could not check tables: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing complete database schema...")
    print("-" * 50)
    
    tables_ok = check_all_tables()
    if tables_ok:
        schema_test_ok = test_complete_schema()
        
        if schema_test_ok:
            print("-" * 50)
            print("🎉 Complete schema test passed!")
            print("✅ Database is ready for the portfolio platform!")
        else:
            print("⚠️  Schema test failed")
    else:
        print("⚠️  Missing required tables")
