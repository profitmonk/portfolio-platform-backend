"""Add unique constraint on symbol and date

Revision ID: 49539542e41b
Revises: 0f660e205a17
Create Date: 2025-07-14 15:12:52.246827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49539542e41b'
down_revision: Union[str, None] = '0f660e205a17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    """Add unique constraint on symbol and date"""
    # First, remove any existing duplicates (if any)
    op.execute("""
        DELETE FROM asset_prices a1 
        USING asset_prices a2 
        WHERE a1.id > a2.id 
        AND a1.symbol = a2.symbol 
        AND a1.date = a2.date
    """)
    
    # Add the unique constraint
    op.create_unique_constraint(
        'uq_asset_prices_symbol_date',
        'asset_prices', 
        ['symbol', 'date']
    )

def downgrade():
    """Remove unique constraint"""
    op.drop_constraint(
        'uq_asset_prices_symbol_date', 
        'asset_prices', 
        type_='unique'
    )

