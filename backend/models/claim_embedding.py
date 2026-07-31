"""
ClaimEmbedding Model

Stores LIAR training statements with their binary label and
all-MiniLM-L6-v2 sentence embeddings for pgvector similarity search.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app import db


class ClaimEmbedding(db.Model):
    """A single LIAR training statement embedded for retrieval."""
    __tablename__ = 'claim_embeddings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_text = Column(Text, nullable=False)
    label = Column(String(20), nullable=False)  # "reliable" | "unreliable"
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'statement_text': self.statement_text,
            'label': self.label,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ClaimEmbedding {self.id} label={self.label}>'
