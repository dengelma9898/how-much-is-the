"""Initial database schema

Revision ID: e07c67063c73
Revises: 
Create Date: 2025-07-09 21:43:32.142271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e07c67063c73'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stores table
    op.create_table('stores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('logo_url', sa.String(length=255), nullable=True),
        sa.Column('base_url', sa.String(length=255), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_stores')
    )

    # Create crawl_sessions table
    op.create_table('crawl_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='running'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_products', sa.Integer(), nullable=False, default=0),
        sa.Column('success_count', sa.Integer(), nullable=False, default=0),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], name='fk_crawl_sessions_store_id_stores'),
        sa.PrimaryKeyConstraint('id', name='pk_crawl_sessions')
    )

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('store_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('availability', sa.Boolean(), nullable=False, default=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('product_url', sa.String(length=500), nullable=True),
        sa.Column('postal_code', sa.String(length=10), nullable=True),
        sa.Column('crawl_session_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], name='fk_products_store_id_stores'),
        sa.ForeignKeyConstraint(['crawl_session_id'], ['crawl_sessions.id'], name='fk_products_crawl_session_id_crawl_sessions'),
        sa.PrimaryKeyConstraint('id', name='pk_products')
    )

    # Create indexes for performance
    op.create_index('idx_products_store_name', 'products', ['store_id', 'name'])
    op.create_index('idx_products_price', 'products', ['price'])
    op.create_index('idx_products_category', 'products', ['category'])
    op.create_index('idx_products_postal_code', 'products', ['postal_code'])
    op.create_index('idx_products_availability', 'products', ['availability'])
    op.create_index('idx_products_deleted_at', 'products', ['deleted_at'])
    op.create_index('idx_products_created_at', 'products', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_products_created_at', 'products')
    op.drop_index('idx_products_deleted_at', 'products')
    op.drop_index('idx_products_availability', 'products')
    op.drop_index('idx_products_postal_code', 'products')
    op.drop_index('idx_products_category', 'products')
    op.drop_index('idx_products_price', 'products')
    op.drop_index('idx_products_store_name', 'products')
    
    # Drop tables in reverse order due to foreign keys
    op.drop_table('products')
    op.drop_table('crawl_sessions')
    op.drop_table('stores')
