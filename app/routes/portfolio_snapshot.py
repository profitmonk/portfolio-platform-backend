from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timezone
import csv
import io
from datetime import datetime

from app.database.connection import get_db
from app.models.portfolio import Portfolio
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.user import User
from app.schemas.portfolio_snapshot import (
    PortfolioSnapshotCreate, 
    PortfolioSnapshotResponse, 
    CSVUploadResponse
)
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/portfolios", tags=["Portfolio Snapshots"])

@router.post("/{portfolio_id}/snapshots", response_model=PortfolioSnapshotResponse)
async def create_portfolio_snapshot(
    portfolio_id: int,
    snapshot_data: PortfolioSnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new portfolio snapshot (rebalancing)"""
    
    # Check if portfolio exists and belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Check if snapshot date is not in the future
    if snapshot_data.snapshot_date > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snapshot date cannot be in the future"
        )
    
    # Check if there's already a snapshot for this exact date
    existing_snapshot = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.portfolio_id == portfolio_id,
        func.date(PortfolioSnapshot.snapshot_date) == func.date(snapshot_data.snapshot_date)
    ).first()
    
    if existing_snapshot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A snapshot already exists for this date"
        )
    
    # Create new snapshot
    new_snapshot = PortfolioSnapshot(
        portfolio_id=portfolio_id,
        snapshot_date=snapshot_data.snapshot_date,
        assets=snapshot_data.assets,
        weights=snapshot_data.weights,
        notes=snapshot_data.notes,
        created_by_user_id=current_user.id
    )
    
    db.add(new_snapshot)
    
    # Update portfolio's historical_start_date if this is the first snapshot
    if not portfolio.historical_start_date:
        portfolio.historical_start_date = snapshot_data.snapshot_date
    
    db.commit()
    db.refresh(new_snapshot)
    
    return new_snapshot

@router.get("/{portfolio_id}/snapshots", response_model=List[PortfolioSnapshotResponse])
async def get_portfolio_snapshots(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all snapshots for a portfolio"""
    
    # Check if portfolio exists and is accessible
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Check permissions (owner or public portfolio)
    if portfolio.user_id != current_user.id and not portfolio.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.portfolio_id == portfolio_id
    ).order_by(PortfolioSnapshot.snapshot_date.asc()).all()
    
    return snapshots

@router.post("/{portfolio_id}/snapshots/upload-csv", response_model=CSVUploadResponse)
async def upload_portfolio_csv(
    portfolio_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a CSV file to create multiple portfolio snapshots"""
    
    # Check if portfolio exists and belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    try:
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        #print(f"DEBUG CSV Headers: {csv_reader.fieldnames}")
        
        snapshots_created = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
            try:
                # DEBUG: Print what we're getting from each row
                #print(f"DEBUG Row {row_num}: {dict(row)}")
                #print(f"DEBUG Start Date value: '{row['Start Date']}'")
                # Parse date (expecting format like "2024-01-01")
                snapshot_date = datetime.strptime(row['Start Date'].strip(), '%m/%d/%Y')
                #print(f"DEBUG Parsed date: {snapshot_date}")
                
                # Check if snapshot already exists
                existing = db.query(PortfolioSnapshot).filter(
                    PortfolioSnapshot.portfolio_id == portfolio_id,
                    func.date(PortfolioSnapshot.snapshot_date) == func.date(snapshot_date)
                ).first()
                
                if existing:
                    errors.append(f"Row {row_num}: Snapshot for {snapshot_date.date()} already exists")
                    continue
                # Clean the data FIRST
                # Handle assets with extra spaces and quotes
                assets_raw = row['Assets'].replace('"', '').split(',')
                assets_cleaned = [a.strip() for a in assets_raw if a.strip()]
                assets_string = ','.join(assets_cleaned)
                
                # Handle weights with extra spaces, quotes, and percentages
                weights_raw = row['Weights'].replace('"', '').split(',')
                weights_cleaned = [w.strip().replace('%', '') for w in weights_raw if w.strip()]
                weights_string = ','.join(weights_cleaned)
                
                # Create snapshot with CLEANED data
                snapshot = PortfolioSnapshot(
                    portfolio_id=portfolio_id,
                    snapshot_date=snapshot_date,
                    assets=assets_string,    # Clean data without quotes
                    weights=weights_string,  # Clean data without % symbols
                    created_by_user_id=current_user.id
                )
                
                # Validate the cleaned data
                try:
                    # Convert to proper types for validation
                    assets = assets_cleaned
                    weights = [float(w) for w in weights_cleaned] 
                    
                    if len(assets) != len(weights):
                        errors.append(f"Row {row_num}: Asset count doesn't match weight count")
                        continue
                    
                    weight_sum = sum(weights)
                    if not (99.0 <= weight_sum <= 101.0):
                        errors.append(f"Row {row_num}: Weights sum to {weight_sum}%, should be ~100%")
                        continue
                    
                except ValueError as e:
                    errors.append(f"Row {row_num}: Invalid data - {str(e)}")
                    continue
                
                db.add(snapshot)
                snapshots_created += 1
                
            except Exception as e:
                # REPLACE THIS ENTIRE BLOCK
                error_msg = f"Row {row_num}: {type(e).__name__}: {str(e)}"
                errors.append(error_msg)
                #print(f"DEBUG ERROR - {error_msg}")
        
        # Update portfolio's historical_start_date if this is the first data
        if snapshots_created > 0 and not portfolio.historical_start_date:
            first_snapshot = db.query(PortfolioSnapshot).filter(
                PortfolioSnapshot.portfolio_id == portfolio_id
            ).order_by(PortfolioSnapshot.snapshot_date.asc()).first()
            
            if first_snapshot:
                portfolio.historical_start_date = first_snapshot.snapshot_date
        
        db.commit()
        
        return CSVUploadResponse(
            message=f"Successfully processed CSV file",
            snapshots_created=snapshots_created,
            portfolio_id=portfolio_id,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing CSV file: {str(e)}"
        )
