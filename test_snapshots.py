from app.database.connection import get_db
from app.models.portfolio import Portfolio
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.asset_price import AssetPrice
from datetime import datetime

def test_schema():
    db = next(get_db())
    
    # Test creating a portfolio with snapshots
    portfolio = Portfolio(
        user_id=1,  # Assuming you have a user with ID 1
        name="Test Portfolio",
        description="Testing snapshot system",
        verification_status="unverified",
        initial_balance=100000.0
    )
    
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    # Test creating a snapshot
    snapshot = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        snapshot_date=datetime.now(),
        assets="AAPL,MSFT,TSLA",
        weights="50,30,20",
        created_by_user_id=1
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    print(f"✅ Portfolio created: {portfolio.name}")
    print(f"✅ Snapshot created: {snapshot.allocation_dict}")
    print(f"✅ Asset list: {snapshot.asset_list}")
    print(f"✅ Weight list: {snapshot.weight_list}")
    
    # Clean up in correct order: snapshots first, then portfolio
    db.delete(snapshot)
    db.commit()  # Commit snapshot deletion first
    
    db.delete(portfolio)
    db.commit()  # Then commit portfolio deletion
    
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    test_schema()
