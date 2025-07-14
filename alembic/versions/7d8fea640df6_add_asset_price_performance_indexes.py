"""Add asset price performance indexes

Revision ID: 7d8fea640df6
Revises: 828cc12b3d43
Create Date: 2025-07-13 11:31:15.476144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d8fea640df6'
down_revision: Union[str, None] = '828cc12b3d43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade():
    """Add performance indexes to asset_prices table"""
    # Create composite index on (symbol, date) for symbol-specific queries
    op.create_index(
        'idx_symbol_date', 
        'asset_prices', 
        ['symbol', 'date']
    )
    
    # Create composite index on (date, symbol) for date-range queries
    op.create_index(
        'idx_date_symbol', 
        'asset_prices', 
        ['date', 'symbol']
    )
    
    print("✅ Added performance indexes to asset_prices table")

def downgrade():
    """Remove the indexes if needed"""
    op.drop_index('idx_symbol_date', table_name='asset_prices')
    op.drop_index('idx_date_symbol', table_name='asset_prices')
    
    print("🗑️ Removed indexes from asset_prices table")
