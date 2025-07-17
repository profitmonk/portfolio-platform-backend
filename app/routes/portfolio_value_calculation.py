from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.portfolio import Portfolio
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.asset_price import AssetPrice
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter()

class CalculateValuesRequest(BaseModel):
    starting_value: float = 100000.0
    recalculate: bool = True

class CalculationResult(BaseModel):
    success: bool
    values_calculated: int
    errors: List[str]

@router.post("/portfolios/{portfolio_id}/calculate-values", response_model=CalculationResult)
async def calculate_portfolio_values(
    portfolio_id: int,
    request: CalculateValuesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate real portfolio values using market data"""
    
    # Verify portfolio ownership
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get all snapshots for this portfolio
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.portfolio_id == portfolio_id
    ).order_by(PortfolioSnapshot.snapshot_date).all()
    
    if not snapshots:
        raise HTTPException(status_code=400, detail="No snapshots found for this portfolio")
    
    logging.info(f"Calculating values for {len(snapshots)} snapshots")
    
    # Get all unique symbols
    all_symbols = set()
    for snapshot in snapshots:
        if snapshot.assets:
            symbols = [s.strip().upper() for s in snapshot.assets.split(',')]
            all_symbols.update(symbols)
    
    logging.info(f"Symbols needed: {list(all_symbols)}")
    
    # Get date range
    start_date = snapshots[0].snapshot_date.date()
    end_date = datetime.now().date()
    
    # Fetch price data for all symbols in date range
    price_data = {}
    missing_symbols = []
    
    for symbol in all_symbols:
        prices = db.query(AssetPrice).filter(
            AssetPrice.symbol == symbol,
            AssetPrice.date >= start_date,
            AssetPrice.date <= end_date
        ).all()
        
        if prices:
            price_data[symbol] = {p.date.strftime('%Y-%m-%d'): p.adjusted_close for p in prices}
            logging.info(f"Found {len(prices)} prices for {symbol}")
        else:
            missing_symbols.append(symbol)
            logging.warning(f"No price data found for symbol: {symbol}")
    
    # Calculate portfolio values
    calculated_values = 0
    errors = []
    current_value = request.starting_value
    
    for i, snapshot in enumerate(snapshots):
        try:
            snapshot_date = snapshot.snapshot_date.date().strftime('%Y-%m-%d')
            
            # Parse assets and weights
            if not snapshot.assets or not snapshot.weights:
                errors.append(f"Snapshot {i+1}: Missing assets or weights")
                continue
                
            assets = [s.strip().upper() for s in snapshot.assets.split(',')]
            weights = [float(w.strip()) for w in snapshot.weights.split(',')]
            
            if len(assets) != len(weights):
                errors.append(f"Snapshot {i+1}: Asset/weight count mismatch")
                continue
            
            # Calculate portfolio value for this date
            portfolio_value = 0
            valid_allocations = 0
            
            for asset, weight in zip(assets, weights):
                if asset in price_data:
                    # Find closest price to snapshot date
                    price = find_closest_price(price_data[asset], snapshot_date)
                    if price:
                        # Calculate allocation value (weight as percentage)
                        allocation_value = current_value * (weight / 100.0)
                        portfolio_value += allocation_value
                        valid_allocations += 1
                    else:
                        errors.append(f"Snapshot {i+1}: No price data for {asset} near {snapshot_date}")
                else:
                    errors.append(f"Snapshot {i+1}: Missing price data for {asset}")
            
            # Update snapshot with calculated value if we have valid data
            if valid_allocations > 0 and portfolio_value > 0:
                snapshot.total_value = portfolio_value
                calculated_values += 1
                current_value = portfolio_value
                
                # Update portfolio's latest values
                portfolio.total_value = portfolio_value
                if i == 0:  # First snapshot
                    portfolio.total_return_percentage = 0.0
                else:
                    portfolio.total_return_percentage = ((portfolio_value - request.starting_value) / request.starting_value) * 100
                    
                logging.info(f"Snapshot {i+1}: Calculated value ${portfolio_value:,.2f}")
            else:
                errors.append(f"Snapshot {i+1}: Could not calculate value - no valid price data")
            
        except Exception as e:
            errors.append(f"Snapshot {i+1}: Error - {str(e)}")
            logging.error(f"Error in snapshot {i+1}: {e}")
    
    # Commit changes
    try:
        db.commit()
        logging.info(f"Successfully calculated {calculated_values} portfolio values")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save calculations: {str(e)}")
    
    return CalculationResult(
        success=True,
        values_calculated=calculated_values,
        errors=errors
    )

def find_closest_price(price_dict: Dict[str, float], target_date: str) -> Optional[float]:
    """Find the closest available price to target date within 7 days"""
    if target_date in price_dict:
        return price_dict[target_date]
    
    target = datetime.strptime(target_date, '%Y-%m-%d')
    
    # Search within 7 days
    for days_offset in range(1, 8):
        # Try before target date
        before_date = (target - timedelta(days=days_offset)).strftime('%Y-%m-%d')
        if before_date in price_dict:
            return price_dict[before_date]
        
        # Try after target date
        after_date = (target + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        if after_date in price_dict:
            return price_dict[after_date]
    
    return None
