from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class PostType(enum.Enum):
    PORTFOLIO = "portfolio"
    TEXT = "text"
    IMAGE = "image"
    AUTO_PERFORMANCE = "auto_performance"
    AUTO_NEW_HOLDING = "auto_new_holding"
    AUTO_MILESTONE = "auto_milestone"

class Visibility(enum.Enum):
    PUBLIC = "public"
    FOLLOWERS = "followers"
    PRIVATE = "private"

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Content
    post_type = Column(Enum(PostType), nullable=False)
    content_text = Column(Text, nullable=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    holding_id = Column(Integer, ForeignKey("holdings.id"), nullable=True)
    image_url = Column(String, nullable=True)
    
    # Settings
    auto_generated = Column(Boolean, default=False)
    visibility = Column(Enum(Visibility), default=Visibility.PUBLIC)
    
    # Social metrics
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="posts")
    portfolio = relationship("Portfolio")
    holding = relationship("Holding")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    #Activate later 
    #likes = relationship("Like", primaryjoin="and_(Post.id==Like.likeable_id, Like.likeable_type=='post')", cascade="all, delete-orphan")
