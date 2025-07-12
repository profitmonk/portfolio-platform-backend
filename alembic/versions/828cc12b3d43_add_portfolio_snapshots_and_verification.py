"""add_portfolio_snapshots_and_verification

Revision ID: 828cc12b3d43
Revises: 04c963d66174
Create Date: 2025-07-10 16:24:11.221464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '828cc12b3d43'
down_revision: Union[str, None] = '04c963d66174'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Add new columns to portfolios table
    op.add_column('portfolios', sa.Column('verification_status', sa.String(), nullable=True, server_default='unverified'))
    op.add_column('portfolios', sa.Column('real_time_start_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('portfolios', sa.Column('trust_score', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('portfolios', sa.Column('historical_start_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('portfolios', sa.Column('initial_balance', sa.Float(), nullable=True, server_default='100000.0'))
    op.add_column('portfolios', sa.Column('rebalancing_frequency', sa.String(), nullable=True, server_default='flexible'))
    
    # Create portfolio_snapshots table
    op.create_table('portfolio_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assets', sa.Text(), nullable=False),
        sa.Column('weights', sa.Text(), nullable=False),
        sa.Column('total_value', sa.Float(), nullable=True, server_default='100000.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolio_snapshots_id'), 'portfolio_snapshots', ['id'], unique=False)
    
    # Create asset_prices table
    op.create_table('asset_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open_price', sa.Float(), nullable=True),
        sa.Column('high_price', sa.Float(), nullable=True),
        sa.Column('low_price', sa.Float(), nullable=True),
        sa.Column('close_price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('data_source', sa.String(), nullable=True, server_default='financialmodelingprep'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('symbol', 'date', name='unique_symbol_date'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_prices_id'), 'asset_prices', ['id'], unique=False)
    op.create_index(op.f('ix_asset_prices_symbol'), 'asset_prices', ['symbol'], unique=False)
    op.create_index(op.f('ix_asset_prices_date'), 'asset_prices', ['date'], unique=False)

def downgrade():
    # Drop new tables
    op.drop_table('asset_prices')
    op.drop_table('portfolio_snapshots')
    
    # Remove new columns from portfolios
    op.drop_column('portfolios', 'rebalancing_frequency')
    op.drop_column('portfolios', 'initial_balance')
    op.drop_column('portfolios', 'historical_start_date')
    op.drop_column('portfolios', 'trust_score')
    op.drop_column('portfolios', 'real_time_start_date')
    op.drop_column('portfolios', 'verification_status')
