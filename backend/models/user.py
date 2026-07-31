"""
User Model
"""
import uuid
from datetime import datetime
import bcrypt
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app import db
from models.guid import GUID


class User(db.Model):
    """User account model for authentication and analysis history."""
    __tablename__ = 'users'

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    analyses = relationship('AnalysisRecord', back_populates='user', cascade='all, delete-orphan')
    feedbacks = relationship('UserFeedback', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Set password hash from plain text password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the hash."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.password_hash.encode('utf-8')
            )
        except Exception:
            return False

    def to_dict(self, include_email=False):
        """Convert to dictionary for API responses."""
        result = {
            'id': str(self.id),
            'username': self.username,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_email:
            result['email'] = self.email
        return result

    def __repr__(self):
        return f'<User {self.email}>'