from sqlalchemy import Column, Integer, String, DateTime, Float, UniqueConstraint
from sqlalchemy.sql import func
from app.database.connection import Base

class AssetPrice(Base):
    __tablename__ = "asset_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Asset identification
    symbol = Column(String, nullable=False, index=True)  # AAPL, MSFT, etc.
    
    # Price data
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)  # Main price we'll use
    volume = Column(Float, nullable=True)
    
    # Data source tracking
    data_source = Column(String, default="financialmodelingprep")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure one price per symbol per date
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='unique_symbol_date'),
    )
