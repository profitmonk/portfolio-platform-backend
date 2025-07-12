from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from app.models.holding import AssetType
from app.schemas.portfolio_snapshot import PortfolioSnapshotResponse

# Portfolio Schemas
class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = False

class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None

class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_public: bool
    is_model_portfolio: bool
    
    # Calculated values
    total_value: float
    total_cost_basis: float
    total_return_amount: float
    total_return_percentage: float
    daily_return_amount: float
    daily_return_percentage: float
    
    # Risk metrics
    volatility: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    last_calculated: Optional[datetime]
    
    # User info
    owner_username: Optional[str] = None
    follower_count: int = 0
    holdings_count: int = 0

    # Add to your existing PortfolioResponse schema:
    verification_status: str = "unverified"
    real_time_start_date: Optional[datetime] = None
    trust_score: float = 0.0
    historical_start_date: Optional[datetime] = None
    initial_balance: float = 100000.0
    rebalancing_frequency: str = "flexible"
    
    # Add snapshots to the response
    snapshots: List[PortfolioSnapshotResponse] = []
    
    class Config:
        from_attributes = True

# Holding Schemas
class HoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    asset_type: AssetType
    asset_name: Optional[str] = Field(None, max_length=200)
    quantity: float = Field(..., gt=0)
    average_cost: float = Field(..., gt=0)
    purchase_date: Optional[datetime] = None

class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    average_cost: Optional[float] = Field(None, gt=0)
    asset_name: Optional[str] = Field(None, max_length=200)

class HoldingResponse(BaseModel):
    id: int
    symbol: str
    asset_type: AssetType
    asset_name: Optional[str]
    
    # Position information
    quantity: float
    average_cost: float
    current_price: float
    
    # Calculated values
    total_cost_basis: float
    current_value: float
    unrealized_gain_loss: float
    unrealized_return_percentage: float
    
    # Dates
    purchase_date: datetime
    last_price_update: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Performance Schemas
class PerformanceResponse(BaseModel):
    date: date
    total_value: float
    total_cost_basis: float
    total_return_amount: float
    total_return_percentage: float
    daily_return_amount: float
    daily_return_percentage: float
    volatility_30d: Optional[float]
    sp500_return: Optional[float]
    
    class Config:
        from_attributes = True

class PortfolioDetailResponse(PortfolioResponse):
    holdings: List[HoldingResponse] = []
    recent_performance: List[PerformanceResponse] = []
