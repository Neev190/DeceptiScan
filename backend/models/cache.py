"""
Cached Analysis Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from app import db
from models.guid import GUID

JSONB = JSON().with_variant(PG_JSONB, 'postgresql')


class CachedAnalysis(db.Model):
    """Cached analysis results for quick retrieval."""
    __tablename__ = 'cached_analyses'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hash
    input_text = Column(Text, nullable=False)  # Store text for reference
    source_url = Column(String(2048), nullable=True)
    result = Column(JSONB, nullable=False)  # Cached analysis result
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def is_expired(self):
        """Check if the cached result has expired."""
        return datetime.utcnow() > self.expires_at

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': str(self.id),
            'content_hash': self.content_hash,
            'input_text': self.input_text,
            'source_url': self.source_url,
            'result': self.result,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<CachedAnalysis {self.id} hash={self.content_hash[:8]}...>'

    # Clean up expired cache entries periodically
    __table_args__ = (
        Index('idx_cached_expires_at', 'expires_at'),
    )