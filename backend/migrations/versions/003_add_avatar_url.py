"""Add avatar_url column to users table

Revision ID: 003_add_avatar_url
Revises: 002_retrieval_corpus
Create Date: 2026-08-15 00:00:00

This migration:
1. Adds nullable avatar_url VARCHAR(500) column to the users table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_avatar_url'
down_revision: Union[str, None] = '002_retrieval_corpus'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('avatar_url', sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
