from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class HistoricalPerformance(Base):
    __tablename__ = "historical_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Daily snapshot values
    total_value = Column(Float, nullable=False)
    total_cost_basis = Column(Float, nullable=False)
    total_return_amount = Column(Float, nullable=False)
    total_return_percentage = Column(Float, nullable=False)
    
    # Daily change
    daily_return_amount = Column(Float, default=0.0)
    daily_return_percentage = Column(Float, default=0.0)
    
    # Risk metrics (calculated periodically)
    volatility_30d = Column(Float, nullable=True)  # 30-day rolling volatility
    
    # Market comparison (optional)
    sp500_return = Column(Float, nullable=True)  # S&P 500 return for comparison
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships (we'll activate these after updating other models)
    # portfolio = relationship("Portfolio", back_populates="performance_history")
    
    # Ensure one record per portfolio per date
    __table_args__ = (UniqueConstraint('portfolio_id', 'date', name='_portfolio_date_uc'),)
