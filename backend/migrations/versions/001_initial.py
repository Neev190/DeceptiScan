"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_admin', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create analysis_records table
    op.create_table(
        'analysis_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(2048), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('authenticity_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('classification', sa.String(50), nullable=False),
        sa.Column('sentence_results', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('is_cached', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_analysis_records_user_id', 'analysis_records', ['user_id'])
    op.create_index('idx_analysis_user_created', 'analysis_records', ['user_id', 'created_at'])
    op.create_index('idx_analysis_created_at', 'analysis_records', ['created_at'])
    
    # Create user_feedbacks table
    op.create_table(
        'user_feedbacks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('analysis_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('corrected_classification', sa.String(50), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_user_feedbacks_analysis_id', 'user_feedbacks', ['analysis_id'])
    op.create_index('ix_user_feedbacks_user_id', 'user_feedbacks', ['user_id'])
    
    # Create cached_analyses table
    op.create_table(
        'cached_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(2048), nullable=True),
        sa.Column('result', postgresql.JSONB(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_cached_analyses_content_hash', 'cached_analyses', ['content_hash'])
    op.create_index('idx_cached_expires_at', 'cached_analyses', ['expires_at'])


def downgrade() -> None:
    op.drop_table('cached_analyses')
    op.drop_table('user_feedbacks')
    op.drop_table('analysis_records')
    op.drop_table('users')