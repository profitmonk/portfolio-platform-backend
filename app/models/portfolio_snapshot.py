from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Snapshot data
    snapshot_date = Column(DateTime(timezone=True), nullable=False)  # When this allocation was effective
    assets = Column(Text, nullable=False)  # Comma-separated: "AAPL,MSFT,TSLA"
    weights = Column(Text, nullable=False)  # Comma-separated: "50,30,20"
    
    # Calculated values at time of snapshot
    total_value = Column(Float, default=100000.0)  # Starts at $100K
    notes = Column(Text, nullable=True)  # Optional rebalancing notes
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # When user entered this
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    #portfolio = relationship("Portfolio", back_populates="snapshots")
    #created_by = relationship("User")
    
    @property
    def asset_list(self):
        """Convert comma-separated assets to list"""
        return [asset.strip() for asset in self.assets.split(',') if asset.strip()]
    
    @property
    def weight_list(self):
        """Convert comma-separated weights to list of floats"""
        return [float(weight.strip()) for weight in self.weights.split(',') if weight.strip()]
    
    @property
    def allocation_dict(self):
        """Return dict of asset: weight pairs"""
        assets = self.asset_list
        weights = self.weight_list
        return dict(zip(assets, weights)) if len(assets) == len(weights) else {}
