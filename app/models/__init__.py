# Import all models so they are registered with SQLAlchemy
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.holding import Holding, AssetType
from app.models.historical_performance import HistoricalPerformance
from app.models.follow import Follow

# Import Base for migrations
from app.database.connection import Base

__all__ = [
    "User",
    "Portfolio", 
    "Holding",
    "AssetType",
    "HistoricalPerformance",
    "Follow",
    "Base"
]
