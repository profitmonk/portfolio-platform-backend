from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class LikeableType(enum.Enum):
    POST = "post"
    COMMENT = "comment"
    PORTFOLIO = "portfolio"

class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    likeable_type = Column(Enum(LikeableType), nullable=False)
    likeable_id = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Ensure user can only like something once
    __table_args__ = (UniqueConstraint('user_id', 'likeable_type', 'likeable_id', name='_user_like_uc'),)
