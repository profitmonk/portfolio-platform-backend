from pydantic import BaseModel, validator
from datetime import datetime
from typing import List, Dict, Optional

class PortfolioSnapshotBase(BaseModel):
    snapshot_date: datetime
    assets: str  # "AAPL,MSFT,TSLA"
    weights: str  # "50,30,20"
    notes: Optional[str] = None

    @validator('assets')
    def validate_assets(cls, v):
        assets = [asset.strip() for asset in v.split(',') if asset.strip()]
        if not assets:
            raise ValueError('At least one asset is required')
        return v

    @validator('weights')
    def validate_weights(cls, v, values):
        weights = [weight.strip() for weight in v.split(',') if weight.strip()]
        if not weights:
            raise ValueError('Weights are required')
        
        # Check if weights can be converted to floats
        try:
            weight_floats = [float(w) for w in weights]
        except ValueError:
            raise ValueError('All weights must be valid numbers')
        
        # Check if assets and weights match in count
        if 'assets' in values:
            assets = [asset.strip() for asset in values['assets'].split(',') if asset.strip()]
            if len(assets) != len(weights):
                raise ValueError('Number of assets must match number of weights')
        
        # Check if weights sum to approximately 100
        total = sum(weight_floats)
        if not (99.0 <= total <= 101.0):
            raise ValueError('Weights must sum to approximately 100%')
        
        return v

class PortfolioSnapshotCreate(PortfolioSnapshotBase):
    pass

class PortfolioSnapshotUpdate(BaseModel):
    assets: Optional[str] = None
    weights: Optional[str] = None
    notes: Optional[str] = None

class PortfolioSnapshotResponse(PortfolioSnapshotBase):
    id: int
    portfolio_id: int
    total_value: float
    created_at: datetime
    created_by_user_id: int
    
    # Computed properties
    asset_list: List[str]
    weight_list: List[float]
    allocation_dict: Dict[str, float]

    class Config:
        from_attributes = True

    @validator('asset_list', pre=True, always=True)
    def compute_asset_list(cls, v, values):
        if 'assets' in values:
            return [asset.strip() for asset in values['assets'].split(',') if asset.strip()]
        return v

    @validator('weight_list', pre=True, always=True)
    def compute_weight_list(cls, v, values):
        if 'weights' in values:
            return [float(weight.strip()) for weight in values['weights'].split(',') if weight.strip()]
        return v

    @validator('allocation_dict', pre=True, always=True)
    def compute_allocation_dict(cls, v, values):
        if 'assets' in values and 'weights' in values:
            assets = [asset.strip() for asset in values['assets'].split(',') if asset.strip()]
            weights = [float(weight.strip()) for weight in values['weights'].split(',') if weight.strip()]
            return dict(zip(assets, weights))
        return v

# Schema for CSV upload
class CSVUploadResponse(BaseModel):
    message: str
    snapshots_created: int
    portfolio_id: int
    errors: List[str] = []
