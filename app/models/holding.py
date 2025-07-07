from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class AssetType(enum.Enum):
    STOCK = "stock"
    ETF = "etf"
    OPTION = "option"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    BOND = "bond"

class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Asset information
    symbol = Column(String, nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    asset_name = Column(String, nullable=True)  # Full company/asset name
    
    # Position information
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)  # Average cost per share
    current_price = Column(Float, default=0.0)  # Updated daily by ETL
    
    # Calculated values
    total_cost_basis = Column(Float, nullable=False)  # quantity * average_cost
    current_value = Column(Float, default=0.0)  # quantity * current_price
    unrealized_gain_loss = Column(Float, default=0.0)  # current_value - total_cost_basis
    unrealized_return_percentage = Column(Float, default=0.0)
    
    # Position tracking
    purchase_date = Column(DateTime(timezone=True), nullable=False)
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (we'll activate these after updating other models)
    # portfolio = relationship("Portfolio", back_populates="holdings")
    
    def calculate_values(self):
        """Calculate derived values based on current data"""
        self.total_cost_basis = self.quantity * self.average_cost
        self.current_value = self.quantity * self.current_price
        self.unrealized_gain_loss = self.current_value - self.total_cost_basis
        
        if self.total_cost_basis > 0:
            self.unrealized_return_percentage = (self.unrealized_gain_loss / self.total_cost_basis) * 100
        else:
            self.unrealized_return_percentage = 0.0
