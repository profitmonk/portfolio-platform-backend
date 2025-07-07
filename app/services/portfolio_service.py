from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.holding import Holding, AssetType
from app.models.historical_performance import HistoricalPerformance
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate, HoldingCreate, HoldingUpdate
from datetime import datetime, date

class PortfolioService:
    
    @staticmethod
    def create_portfolio(db: Session, portfolio_data: PortfolioCreate, user_id: int) -> Portfolio:
        """Create a new portfolio for a user"""
        portfolio = Portfolio(
            user_id=user_id,
            name=portfolio_data.name,
            description=portfolio_data.description,
            is_public=portfolio_data.is_public
        )
        
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        return portfolio
    
    @staticmethod
    def get_user_portfolios(db: Session, user_id: int) -> List[Portfolio]:
        """Get all portfolios for a user"""
        return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    
    @staticmethod
    def get_portfolio_by_id(db: Session, portfolio_id: int, user_id: Optional[int] = None) -> Portfolio:
        """Get a portfolio by ID with access control"""
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Check access permissions
        if user_id is not None:
            # User is authenticated
            if portfolio.user_id != user_id and not portfolio.is_public:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to private portfolio"
                )
        else:
            # User is not authenticated, can only see public portfolios
            if not portfolio.is_public:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to view private portfolio"
                )
        
        return portfolio
    
    @staticmethod
    def update_portfolio(db: Session, portfolio_id: int, portfolio_data: PortfolioUpdate, user_id: int) -> Portfolio:
        """Update a portfolio (only owner can update)"""
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id, 
            Portfolio.user_id == user_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found or access denied"
            )
        
        # Update fields that are provided
        if portfolio_data.name is not None:
            portfolio.name = portfolio_data.name
        if portfolio_data.description is not None:
            portfolio.description = portfolio_data.description
        if portfolio_data.is_public is not None:
            portfolio.is_public = portfolio_data.is_public
        
        portfolio.updated_at = datetime.now()
        db.commit()
        db.refresh(portfolio)
        return portfolio
    
    @staticmethod
    def delete_portfolio(db: Session, portfolio_id: int, user_id: int):
        """Delete a portfolio (only owner can delete)"""
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id, 
            Portfolio.user_id == user_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found or access denied"
            )
        
        db.delete(portfolio)
        db.commit()
        return {"message": "Portfolio deleted successfully"}
    
    @staticmethod
    def add_holding(db: Session, portfolio_id: int, holding_data: HoldingCreate, user_id: int) -> Holding:
        """Add a holding to a portfolio"""
        # Verify user owns the portfolio
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id, 
            Portfolio.user_id == user_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found or access denied"
            )
        
        # Check if holding already exists for this symbol
        existing_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio_id,
            Holding.symbol == holding_data.symbol.upper()
        ).first()
        
        if existing_holding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Holding for {holding_data.symbol} already exists in this portfolio"
            )
        
        # Create new holding
        holding = Holding(
            portfolio_id=portfolio_id,
            symbol=holding_data.symbol.upper(),
            asset_type=holding_data.asset_type,
            asset_name=holding_data.asset_name,
            quantity=holding_data.quantity,
            average_cost=holding_data.average_cost,
            current_price=holding_data.average_cost,  # Initialize with purchase price
            purchase_date=holding_data.purchase_date or datetime.now()
        )
        
        # Calculate values
        holding.calculate_values()
        
        db.add(holding)
        db.commit()
        db.refresh(holding)
        
        # Update portfolio totals
        PortfolioService.recalculate_portfolio_totals(db, portfolio_id)
        
        return holding
    
    @staticmethod
    def get_portfolio_holdings(db: Session, portfolio_id: int, user_id: Optional[int] = None) -> List[Holding]:
        """Get all holdings for a portfolio"""
        # Verify access to portfolio
        PortfolioService.get_portfolio_by_id(db, portfolio_id, user_id)
        
        return db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
    
    @staticmethod
    def update_holding(db: Session, holding_id: int, holding_data: HoldingUpdate, user_id: int) -> Holding:
        """Update a holding"""
        # Get holding and verify user owns the portfolio
        holding = db.query(Holding).join(Portfolio).filter(
            Holding.id == holding_id,
            Portfolio.user_id == user_id
        ).first()
        
        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holding not found or access denied"
            )
        
        # Update fields
        if holding_data.quantity is not None:
            holding.quantity = holding_data.quantity
        if holding_data.average_cost is not None:
            holding.average_cost = holding_data.average_cost
        if holding_data.asset_name is not None:
            holding.asset_name = holding_data.asset_name
        
        # Recalculate values
        holding.calculate_values()
        holding.updated_at = datetime.now()
        
        db.commit()
        db.refresh(holding)
        
        # Update portfolio totals
        PortfolioService.recalculate_portfolio_totals(db, holding.portfolio_id)
        
        return holding
    
    @staticmethod
    def delete_holding(db: Session, holding_id: int, user_id: int):
        """Delete a holding"""
        # Get holding and verify user owns the portfolio
        holding = db.query(Holding).join(Portfolio).filter(
            Holding.id == holding_id,
            Portfolio.user_id == user_id
        ).first()
        
        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holding not found or access denied"
            )
        
        portfolio_id = holding.portfolio_id
        db.delete(holding)
        db.commit()
        
        # Update portfolio totals
        PortfolioService.recalculate_portfolio_totals(db, portfolio_id)
        
        return {"message": "Holding deleted successfully"}
    
    @staticmethod
    def recalculate_portfolio_totals(db: Session, portfolio_id: int):
        """Recalculate portfolio total values based on holdings"""
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            return
        
        holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
        
        total_cost_basis = sum(holding.total_cost_basis for holding in holdings)
        total_current_value = sum(holding.current_value for holding in holdings)
        total_return_amount = total_current_value - total_cost_basis
        total_return_percentage = (total_return_amount / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        # Update portfolio
        portfolio.total_cost_basis = total_cost_basis
        portfolio.total_value = total_current_value
        portfolio.total_return_amount = total_return_amount
        portfolio.total_return_percentage = total_return_percentage
        portfolio.last_calculated = datetime.now()
        
        db.commit()
    
    @staticmethod
    def get_public_portfolios(db: Session, limit: int = 20, offset: int = 0) -> List[Portfolio]:
        """Get public portfolios for discovery"""
        return db.query(Portfolio).filter(
            Portfolio.is_public == True
        ).order_by(
            Portfolio.total_return_percentage.desc()
        ).offset(offset).limit(limit).all()
