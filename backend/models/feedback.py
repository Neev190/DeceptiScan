"""
User Feedback Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app import db
from models.guid import GUID


class UserFeedback(db.Model):
    """User feedback on analysis results."""
    __tablename__ = 'user_feedbacks'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(GUID, ForeignKey('analysis_records.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    feedback_type = Column(String(50), nullable=False)  # helpful, incorrect, disputed
    corrected_classification = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis = relationship('AnalysisRecord', back_populates='feedbacks')
    user = relationship('User', back_populates='feedbacks')

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': str(self.id),
            'analysis_id': str(self.analysis_id),
            'user_id': str(self.user_id) if self.user_id else None,
            'feedback_type': self.feedback_type,
            'corrected_classification': self.corrected_classification,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<UserFeedback {self.id} type={self.feedback_type}>'