# app/routes/portfolio_value_calculation.py
# Fixed version with PROPER REBALANCING SIMULATION

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel

# Update these imports to match your project structure
try:
    from app.database.connection import get_db
except ImportError:
    try:
        from app.db import get_db
    except ImportError:
        from app.database import SessionLocal
        def get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

try:
    from app.models.portfolio import Portfolio
    from app.models.portfolio_snapshot import PortfolioSnapshot  
    from app.models.asset_price import AssetPrice
    from app.models.user import User
except ImportError:
    from app.database.models import Portfolio, PortfolioSnapshot, AssetPrice, User

try:
    from app.auth.dependencies import get_current_user
except ImportError:
    from app.dependencies import get_current_user

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
    """Calculate real portfolio values using PROPER REBALANCING SIMULATION"""
    
    try:
        # Verify portfolio ownership
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Get all snapshots for this portfolio, sorted by date
        snapshots = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id
        ).order_by(PortfolioSnapshot.snapshot_date).all()
        
        if not snapshots:
            raise HTTPException(status_code=400, detail="No snapshots found for this portfolio")
        
        print(f"Calculating values for {len(snapshots)} rebalancing snapshots")
        
        # Get all unique symbols across all snapshots
        all_symbols = set()
        for snapshot in snapshots:
            if snapshot.assets:
                symbols = [s.strip().upper() for s in snapshot.assets.split(',')]
                all_symbols.update(symbols)
        
        print(f"Symbols needed: {list(all_symbols)}")
        
        # Get date range - from first snapshot to now
        start_date = snapshots[0].snapshot_date.date()
        end_date = datetime.now().date()
        
        # Fetch ALL price data for the entire period
        price_data = {}
        for symbol in all_symbols:
            prices = db.query(AssetPrice).filter(
                AssetPrice.symbol == symbol,
                AssetPrice.date >= start_date,
                AssetPrice.date <= end_date
            ).all()
            
            if prices:
                # Store as {date: price} mapping
                price_data[symbol] = {p.date.strftime('%Y-%m-%d'): p.adjusted_close for p in prices}
                print(f"Found {len(prices)} prices for {symbol}")
            else:
                print(f"WARNING: No price data found for symbol: {symbol}")
        
        # CORE REBALANCING SIMULATION
        portfolio_value = request.starting_value  # Start with $100K
        current_holdings = {}  # Track shares of each asset
        calculated_values = 0
        errors = []
        
        for i, snapshot in enumerate(snapshots):
            try:
                rebalance_date = snapshot.snapshot_date.date().strftime('%Y-%m-%d')
                print(f"\n=== REBALANCE {i+1} on {rebalance_date} ===")
                print(f"Portfolio value before rebalance: ${portfolio_value:,.2f}")
                
                # Parse the new allocation from CSV
                if not snapshot.assets or not snapshot.weights:
                    errors.append(f"Rebalance {i+1}: Missing assets or weights")
                    continue
                    
                new_assets = [s.strip().upper() for s in snapshot.assets.split(',')]
                new_weights = [float(w.strip()) for w in snapshot.weights.split(',')]
                
                if len(new_assets) != len(new_weights):
                    errors.append(f"Rebalance {i+1}: Asset/weight count mismatch")
                    continue
                
                # Verify weights sum to 100%
                weight_sum = sum(new_weights)
                if abs(weight_sum - 100.0) > 0.1:
                    errors.append(f"Rebalance {i+1}: Weights sum to {weight_sum}%, not 100%")
                    # Normalize weights
                    new_weights = [w * 100.0 / weight_sum for w in new_weights]
                
                # STEP 1: SELL ALL CURRENT HOLDINGS
                if current_holdings:
                    print("Selling all current holdings...")
                    portfolio_value = calculate_portfolio_value_on_date(current_holdings, price_data, rebalance_date)
                    print(f"Portfolio value after selling: ${portfolio_value:,.2f}")
                
                # STEP 2: BUY NEW ALLOCATION
                print(f"Buying new allocation: {list(zip(new_assets, new_weights))}")
                new_holdings = {}
                
                for asset, weight_pct in zip(new_assets, new_weights):
                    if asset not in price_data:
                        errors.append(f"Rebalance {i+1}: No price data for {asset}")
                        continue
                    
                    # Find price on rebalance date
                    price = find_closest_price(price_data[asset], rebalance_date)
                    if not price:
                        errors.append(f"Rebalance {i+1}: No price for {asset} near {rebalance_date}")
                        continue
                    
                    # Calculate how much to allocate to this asset
                    allocation_amount = portfolio_value * (weight_pct / 100.0)
                    shares_to_buy = allocation_amount / price
                    new_holdings[asset] = shares_to_buy
                    
                    print(f"  {asset}: {weight_pct:.1f}% = ${allocation_amount:,.2f} = {shares_to_buy:.2f} shares @ ${price:.2f}")
                
                # Update current holdings
                current_holdings = new_holdings
                
                # STEP 3: CALCULATE VALUE AFTER REBALANCING
                new_portfolio_value = calculate_portfolio_value_on_date(current_holdings, price_data, rebalance_date)
                
                # Update snapshot with calculated value
                snapshot.total_value = new_portfolio_value
                calculated_values += 1
                portfolio_value = new_portfolio_value
                
                print(f"Portfolio value after rebalancing: ${portfolio_value:,.2f}")
                
                # Update portfolio summary
                portfolio.total_value = portfolio_value
                if i == 0:
                    portfolio.total_return_percentage = 0.0
                else:
                    portfolio.total_return_percentage = ((portfolio_value - request.starting_value) / request.starting_value) * 100
                
                # STEP 4: CALCULATE INTERMEDIATE VALUES (weekly) until next rebalance
                if i < len(snapshots) - 1:  # Not the last snapshot
                    next_rebalance_date = snapshots[i + 1].snapshot_date.date()
                    intermediate_values = calculate_intermediate_values(
                        current_holdings, price_data, rebalance_date, next_rebalance_date
                    )
                    portfolio_value = intermediate_values[-1] if intermediate_values else portfolio_value
                
            except Exception as e:
                errors.append(f"Rebalance {i+1}: Error - {str(e)}")
                print(f"Error in rebalance {i+1}: {e}")
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully calculated {calculated_values} portfolio values")
        print(f"Final portfolio value: ${portfolio_value:,.2f}")
        print(f"Total return: {((portfolio_value - request.starting_value) / request.starting_value) * 100:.2f}%")
        
        return CalculationResult(
            success=True,
            values_calculated=calculated_values,
            errors=errors
        )
        
    except Exception as e:
        db.rollback()
        print(f"Calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")

def calculate_portfolio_value_on_date(holdings: Dict[str, float], price_data: Dict[str, Dict[str, float]], date: str) -> float:
    """Calculate portfolio value on a specific date given current holdings"""
    total_value = 0.0
    
    for symbol, shares in holdings.items():
        if symbol in price_data:
            price = find_closest_price(price_data[symbol], date)
            if price:
                value = shares * price
                total_value += value
            else:
                print(f"Warning: No price for {symbol} on {date}")
        else:
            print(f"Warning: No price data for {symbol}")
    
    return total_value

def calculate_intermediate_values(holdings: Dict[str, float], price_data: Dict[str, Dict[str, float]], start_date: str, end_date: str) -> List[float]:
    """Calculate portfolio values between rebalancing dates (weekly intervals)"""
    values = []
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate weekly values
    current = start + timedelta(days=7)
    while current < end:
        date_str = current.strftime('%Y-%m-%d')
        value = calculate_portfolio_value_on_date(holdings, price_data, date_str)
        if value > 0:
            values.append(value)
        current += timedelta(days=7)
    
    return values

def find_closest_price(price_dict: Dict[str, float], target_date: str) -> Optional[float]:
    """Find the closest available price to target date within 7 days"""
    if target_date in price_dict:
        return price_dict[target_date]
    
    target = datetime.strptime(target_date, '%Y-%m-%d')
    
    # Search within 7 days (weekends/holidays)
    for days_offset in range(1, 8):
        # Try before target date first (more likely to have data)
        before_date = (target - timedelta(days=days_offset)).strftime('%Y-%m-%d')
        if before_date in price_dict:
            return price_dict[before_date]
        
        # Try after target date
        after_date = (target + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        if after_date in price_dict:
            return price_dict[after_date]
    
    return None

# Test endpoint
@router.get("/portfolios/test-calculation")
async def test_calculation_endpoint():
    return {"message": "Portfolio rebalancing calculation endpoint is working", "status": "ok"}
