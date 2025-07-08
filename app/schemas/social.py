from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.post import PostType, Visibility
from app.models.user_preferences import InvestmentStyle, RiskTolerance

# Post Schemas
class PostCreate(BaseModel):
    post_type: PostType
    content_text: Optional[str] = None
    portfolio_id: Optional[int] = None
    image_url: Optional[str] = None
    visibility: Visibility = Visibility.PUBLIC

class PostUpdate(BaseModel):
    content_text: Optional[str] = None
    visibility: Optional[Visibility] = None

class PostResponse(BaseModel):
    id: int
    user_id: int
    post_type: PostType
    content_text: Optional[str]
    portfolio_id: Optional[int]
    image_url: Optional[str]
    visibility: Visibility
    auto_generated: bool
    like_count: int
    comment_count: int
    view_count: int
    engagement_score: float
    created_at: datetime
    
    # Author info
    author_username: str
    author_display_name: Optional[str]
    author_avatar_url: Optional[str]
    
    # User interaction status
    user_has_liked: bool = False
    
    class Config:
        from_attributes = True

# Comment Schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[int] = None

class CommentResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    parent_comment_id: Optional[int]
    content: str
    like_count: int
    created_at: datetime
    
    # Author info
    author_username: str
    author_display_name: Optional[str]
    
    # User interaction status
    user_has_liked: bool = False
    
    # Nested replies
    replies: List['CommentResponse'] = []
    
    class Config:
        from_attributes = True

# Like Schema
class LikeResponse(BaseModel):
    id: int
    user_id: int
    likeable_type: str
    likeable_id: int
    created_at: datetime

# User Follow Schemas
class UserFollowResponse(BaseModel):
    id: int
    follower_id: int
    following_id: int
    followed_at: datetime
    
    # Following user info
    following_username: str
    following_display_name: Optional[str]
    following_avatar_url: Optional[str]

# User Preferences Schemas
class UserPreferencesCreate(BaseModel):
    investment_style: InvestmentStyle = InvestmentStyle.GROWTH
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    preferred_sectors: List[str] = []

class UserPreferencesResponse(BaseModel):
    id: int
    user_id: int
    investment_style: InvestmentStyle
    risk_tolerance: RiskTolerance
    preferred_sectors: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Feed Response
class FeedResponse(BaseModel):
    posts: List[PostResponse]
    has_more: bool
    next_cursor: Optional[str] = None

# Enhanced User Profile Response
class UserProfileResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    bio: Optional[str]
    bio_extended: Optional[str]
    avatar_url: Optional[str]
    creator_status: bool
    verified_investor: bool
    follower_count: int
    following_count: int
    total_engagement_score: float
    
    # Featured portfolio
    featured_portfolio_id: Optional[int]
    featured_portfolio_name: Optional[str]
    
    # User relationship status
    is_following: bool = False
    is_followed_by: bool = False
    
    created_at: datetime
    
    class Config:
        from_attributes = True

# Update existing schemas to support self-referencing
CommentResponse.model_rebuild()
