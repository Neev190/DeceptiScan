"""Add pgvector extension, claim_embeddings table, and similar_claims column

Revision ID: 002_retrieval_corpus
Revises: 001_initial
Create Date: 2026-07-31 00:00:00

This migration:
1. Enables the pgvector extension (requires pgvector/pgvector:pg15 image)
2. Creates the claim_embeddings table for LIAR-derived retrieval corpus
3. Adds nullable similar_claims JSONB column to analysis_records
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_retrieval_corpus'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Part A — enable pgvector extension
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Part B — create claim_embeddings table
        op.execute("""
            CREATE TABLE claim_embeddings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                statement_text TEXT NOT NULL,
                label VARCHAR(20) NOT NULL,
                embedding vector(384) NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
            );
        """)

        # IVFFlat index for fast approximate cosine similarity search.
        op.execute("""
            CREATE INDEX idx_claim_embeddings_embedding
            ON claim_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)

        # Part C — add similar_claims column to analysis_records
        op.add_column(
            'analysis_records',
            sa.Column('similar_claims', postgresql.JSONB(), nullable=True)
        )
    else:
        # Fallback for non-Postgres (e.g. SQLite test DB)
        op.add_column(
            'analysis_records',
            sa.Column('similar_claims', sa.JSON(), nullable=True)
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.drop_column('analysis_records', 'similar_claims')
        op.execute("DROP TABLE IF EXISTS claim_embeddings;")
        op.execute("DROP EXTENSION IF EXISTS vector;")
    else:
        op.drop_column('analysis_records', 'similar_claims')
