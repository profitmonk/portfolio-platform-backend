from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Portfolio information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Privacy settings
    is_public = Column(Boolean, default=False)
    is_model_portfolio = Column(Boolean, default=False)  # For platform-created portfolios
    
    # Calculated values (updated daily by ETL)
    total_value = Column(Float, default=0.0)
    total_cost_basis = Column(Float, default=0.0)
    total_return_amount = Column(Float, default=0.0)
    total_return_percentage = Column(Float, default=0.0)
    daily_return_amount = Column(Float, default=0.0)
    daily_return_percentage = Column(Float, default=0.0)
    
    # Risk metrics (calculated by backend)
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_calculated = Column(DateTime(timezone=True), nullable=True)
    # Social metrics
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    featured_by_user = Column(Boolean, default=False)
    trending_score = Column(Float, default=0.0)    

    # Relationships (we'll activate these after creating other models)
    # owner = relationship("User", back_populates="portfolios")
    # holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    
    @property
    def holdings_count(self):
        return len(self.holdings) if hasattr(self, 'holdings') else 0
