"""
Analysis Record Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app import db


class AnalysisRecord(db.Model):
    """Analysis record storing misinformation analysis results."""
    __tablename__ = 'analysis_records'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    input_text = Column(Text, nullable=False)
    source_url = Column(String(2048), nullable=True)
    title = Column(String(500), nullable=True)
    authenticity_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    classification = Column(String(50), nullable=False)  # reliable, mixed, unreliable, unknown
    sentence_results = Column(JSONB, nullable=False, default=list)
    processing_time = Column(Float, nullable=True)  # milliseconds
    model_version = Column(String(50), nullable=True)
    is_cached = Column(Integer, default=0)  # 0 = not cached, 1 = cached result
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship('User', back_populates='analyses')
    feedbacks = relationship('UserFeedback', back_populates='analysis', cascade='all, delete-orphan')

    # Indexes for common queries
    __table_args__ = (
        Index('idx_analysis_user_created', 'user_id', 'created_at'),
        Index('idx_analysis_created_at', 'created_at'),
    )

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'input_text': self.input_text,
            'source_url': self.source_url,
            'title': self.title,
            'authenticity_score': self.authenticity_score,
            'confidence': self.confidence,
            'classification': self.classification,
            'sentence_results': self.sentence_results,
            'processing_time': self.processing_time,
            'model_version': self.model_version,
            'is_cached': bool(self.is_cached),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<AnalysisRecord {self.id} score={self.authenticity_score}>'