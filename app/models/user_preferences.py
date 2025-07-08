from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class InvestmentStyle(enum.Enum):
    GROWTH = "growth"
    VALUE = "value"
    DIVIDEND = "dividend"
    TECH = "tech"
    CRYPTO = "crypto"
    ESG = "esg"
    INDEX = "index"

class RiskTolerance(enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Investment preferences
    investment_style = Column(Enum(InvestmentStyle), default=InvestmentStyle.GROWTH)
    risk_tolerance = Column(Enum(RiskTolerance), default=RiskTolerance.MODERATE)
    preferred_sectors = Column(JSON, default=list)  # ['technology', 'healthcare', 'finance']
    
    # Feed algorithm weights
    feed_algorithm_weights = Column(JSON, default=lambda: {
        'performance': 0.4,
        'engagement': 0.3, 
        'following': 0.3
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
