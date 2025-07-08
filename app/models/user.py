from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile information
    display_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # Account settings
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Privacy settings
    public_profile = Column(Boolean, default=True)
    allow_followers = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Social features
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    creator_status = Column(Boolean, default=False)
    featured_portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    bio_extended = Column(Text, nullable=True)
    social_links = Column(JSON, default=dict)  # {'twitter': '@username', 'linkedin': 'url'}
    total_engagement_score = Column(Float, default=0.0)
    verified_investor = Column(Boolean, default=False)    

    # Relationships (we'll add these when we create other models)
    # portfolios = relationship("Portfolio", back_populates="owner")
    posts = relationship("Post", back_populates="author")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    featured_portfolio = relationship("Portfolio", foreign_keys=[featured_portfolio_id])
    
    # User following relationships
    following = relationship("UserFollow", foreign_keys="UserFollow.follower_id")
    followers = relationship("UserFollow", foreign_keys="UserFollow.following_id")    

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
