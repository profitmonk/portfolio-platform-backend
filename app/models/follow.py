from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Follow(Base):
    __tablename__ = "follows"
    
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Timestamps
    followed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships (we'll activate these after updating other models)
    # follower = relationship("User", back_populates="follows")
    # portfolio = relationship("Portfolio", back_populates="followers")
    
    # Ensure user can only follow a portfolio once
    __table_args__ = (UniqueConstraint('follower_id', 'portfolio_id', name='_follower_portfolio_uc'),)
