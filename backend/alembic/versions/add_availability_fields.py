"""add availability_text and offer_valid_until fields

Revision ID: add_availability_fields
Revises: e07c67063c73
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_availability_fields'
down_revision: Union[str, None] = 'e07c67063c73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add availability_text column
    op.add_column('products', sa.Column('availability_text', sa.String(length=255), nullable=True))
    
    # Add offer_valid_until column  
    op.add_column('products', sa.Column('offer_valid_until', sa.String(length=10), nullable=True))
    
    # Add index for offer_valid_until for efficient cleanup queries
    op.create_index('idx_products_offer_valid_until', 'products', ['offer_valid_until'])


def downgrade() -> None:
    # Remove index first
    op.drop_index('idx_products_offer_valid_until', table_name='products')
    
    # Remove columns
    op.drop_column('products', 'offer_valid_until')
    op.drop_column('products', 'availability_text') 