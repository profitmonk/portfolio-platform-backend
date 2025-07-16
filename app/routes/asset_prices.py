from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.database.connection import get_db
from app.models.asset_price import AssetPrice
from app.models.user import User
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/asset-prices", tags=["Asset Prices"])

@router.get("/{symbol}")
async def get_asset_prices(
    symbol: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get historical price data for a symbol"""
    
    query = db.query(AssetPrice).filter(AssetPrice.symbol == symbol.upper())
    
    if start_date:
        query = query.filter(AssetPrice.date >= start_date)
    if end_date:
        query = query.filter(AssetPrice.date <= end_date)
    
    prices = query.order_by(AssetPrice.date.asc()).all()
    
    return [
        {
            "symbol": price.symbol,
            "date": price.date.isoformat(),
            "open_price": price.open_price,
            "high_price": price.high_price,
            "low_price": price.low_price,
            "close_price": price.close_price,
            "adjusted_close": price.adjusted_close,
            "volume": price.volume
        }
        for price in prices
    ]

@router.get("/bulk")
async def get_bulk_asset_prices(
    symbols: str = Query(..., description="Comma-separated symbols"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get bulk historical price data for multiple symbols"""
    
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    
    query = db.query(AssetPrice).filter(AssetPrice.symbol.in_(symbol_list))
    
    if start_date:
        query = query.filter(AssetPrice.date >= start_date)
    if end_date:
        query = query.filter(AssetPrice.date <= end_date)
    
    prices = query.order_by(AssetPrice.symbol, AssetPrice.date.asc()).all()
    
    return [
        {
            "symbol": price.symbol,
            "date": price.date.isoformat(),
            "open_price": price.open_price,
            "high_price": price.high_price,
            "low_price": price.low_price,
            "close_price": price.close_price,
            "adjusted_close": price.adjusted_close,
            "volume": price.volume
        }
        for price in prices
    ]
