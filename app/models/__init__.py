# Import all models so they are registered with SQLAlchemy
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.holding import Holding, AssetType
from app.models.historical_performance import HistoricalPerformance
from app.models.follow import Follow

# Import new social models
from app.models.post import Post, PostType, Visibility
from app.models.comment import Comment
from app.models.like import Like, LikeableType
from app.models.user_follow import UserFollow
from app.models.user_preferences import UserPreferences, InvestmentStyle, RiskTolerance
from app.models.feed_event import FeedEvent, EventType

# Import new portfolio snapshot models
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.asset_price import AssetPrice

# Import Base for migrations
from app.database.connection import Base

__all__ = [
    "User",
    "Portfolio", 
    "Holding",
    "AssetType",
    "HistoricalPerformance",
    "Follow",
    "Post",
    "PostType", 
    "Visibility",
    "Comment",
    "Like",
    "LikeableType",
    "UserFollow",
    "UserPreferences",
    "InvestmentStyle",
    "RiskTolerance", 
    "FeedEvent",
    "EventType",
    "PortfolioSnapshot",
    "AssetPrice",
    "Base"
]
