from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Index, BigInteger
from sqlalchemy.sql import func
from app.database.connection import Base

class AssetPrice(Base):
    __tablename__ = "asset_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # OHLCV data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(BigInteger, default=0)
    adjusted_close = Column(Float, nullable=False)  # Make sure this field exists
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date'),
        Index('idx_date_symbol', 'date', 'symbol'),
    )
