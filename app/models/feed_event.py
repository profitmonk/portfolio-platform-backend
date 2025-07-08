from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class EventType(enum.Enum):
    VIEW = "view"
    LIKE = "like"
    COMMENT = "comment" 
    SHARE = "share"
    PORTFOLIO_VIEW = "portfolio_view"
    FOLLOW = "follow"

class FeedEvent(Base):
    __tablename__ = "feed_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # For follow events
    
    # Event details
    event_type = Column(Enum(EventType), nullable=False)
    engagement_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    post = relationship("Post")
    target_user = relationship("User", foreign_keys=[target_user_id])
