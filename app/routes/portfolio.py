from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioDetailResponse,
    HoldingCreate, HoldingUpdate, HoldingResponse
)
from app.services.portfolio_service import PortfolioService
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/portfolios", tags=["Portfolios"])

# Portfolio endpoints
@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new portfolio"""
    portfolio = PortfolioService.create_portfolio(db, portfolio_data, current_user.id)
    
    # Add user info for response
    response_data = PortfolioResponse.from_orm(portfolio)
    response_data.owner_username = current_user.username
    return response_data

@router.get("/", response_model=List[PortfolioResponse])
async def get_my_portfolios(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's portfolios"""
    portfolios = PortfolioService.get_user_portfolios(db, current_user.id)
    
    response_portfolios = []
    for portfolio in portfolios:
        response_data = PortfolioResponse.from_orm(portfolio)
        response_data.owner_username = current_user.username
        response_data.holdings_count = len(portfolio.holdings) if hasattr(portfolio, 'holdings') else 0
        response_portfolios.append(response_data)
    
    return response_portfolios

@router.get("/public", response_model=List[PortfolioResponse])
async def get_public_portfolios(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get public portfolios for discovery"""
    portfolios = PortfolioService.get_public_portfolios(db, limit, offset)
    
    response_portfolios = []
    for portfolio in portfolios:
        # Get owner username
        owner = db.query(User).filter(User.id == portfolio.user_id).first()
        
        response_data = PortfolioResponse.from_orm(portfolio)
        response_data.owner_username = owner.username if owner else "Unknown"
        response_data.holdings_count = len(portfolio.holdings) if hasattr(portfolio, 'holdings') else 0
        response_portfolios.append(response_data)
    
    return response_portfolios

@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def get_portfolio_detail(
    portfolio_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed portfolio information including holdings"""
    user_id = current_user.id if current_user else None
    portfolio = PortfolioService.get_portfolio_by_id(db, portfolio_id, user_id)
    
    # Get holdings
    holdings = PortfolioService.get_portfolio_holdings(db, portfolio_id, user_id)
    
    # Get owner info
    owner = db.query(User).filter(User.id == portfolio.user_id).first()
    
    # Build response
    response_data = PortfolioDetailResponse.from_orm(portfolio)
    response_data.owner_username = owner.username if owner else "Unknown"
    response_data.holdings_count = len(holdings)
    response_data.holdings = [HoldingResponse.from_orm(holding) for holding in holdings]
    response_data.recent_performance = []  # We'll add this later
    
    return response_data

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a portfolio"""
    portfolio = PortfolioService.update_portfolio(db, portfolio_id, portfolio_data, current_user.id)
    
    response_data = PortfolioResponse.from_orm(portfolio)
    response_data.owner_username = current_user.username
    return response_data

@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a portfolio"""
    return PortfolioService.delete_portfolio(db, portfolio_id, current_user.id)

# Holding endpoints
@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def add_holding(
    portfolio_id: int,
    holding_data: HoldingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a holding to a portfolio"""
    holding = PortfolioService.add_holding(db, portfolio_id, holding_data, current_user.id)
    return HoldingResponse.from_orm(holding)

@router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
async def get_portfolio_holdings(
    portfolio_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all holdings for a portfolio"""
    user_id = current_user.id if current_user else None
    holdings = PortfolioService.get_portfolio_holdings(db, portfolio_id, user_id)
    return [HoldingResponse.from_orm(holding) for holding in holdings]

@router.put("/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    holding_id: int,
    holding_data: HoldingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a holding"""
    holding = PortfolioService.update_holding(db, holding_id, holding_data, current_user.id)
    return HoldingResponse.from_orm(holding)

@router.delete("/holdings/{holding_id}")
async def delete_holding(
    holding_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a holding"""
    return PortfolioService.delete_holding(db, holding_id, current_user.id)
