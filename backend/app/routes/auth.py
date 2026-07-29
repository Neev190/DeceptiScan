"""
Authentication API endpoints for DeceptiScan.
"""
import uuid
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.routes import api_bp
from app.validators import validate_auth_request, ValidationError
from app import db
from models.user import User


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Request Body:
        email (str): User email (required)
        password (str): User password (required, min 8 chars)
    
    Response:
        User ID and access token
    """
    data = request.get_json()
    
    # Validate input
    is_valid, error = validate_auth_request(data)
    if not is_valid:
        return jsonify(error.to_dict()), 400
    
    email = data.get('email').lower().strip()
    password = data.get('password')
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Email is already registered',
            details={'field': 'email'}
        ).to_dict()), 400
    
    # Create new user
    user = User(
        id=uuid.uuid4(),
        email=email,
        created_at=datetime.utcnow(),
        is_active=True
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(ValidationError(
            code='INTERNAL_ERROR',
            message='Failed to create user account',
            details={}
        ).to_dict()), 500
    
    # Generate tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'userId': str(user.id),
        'token': access_token,
        'refreshToken': refresh_token
    }), 201


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """
    User login endpoint.
    
    Request Body:
        email (str): User email (required)
        password (str): User password (required)
    
    Response:
        Access token and user info
    """
    data = request.get_json()
    
    if not data:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Request body is required',
            details={}
        ).to_dict()), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Email and password are required',
            details={}
        ).to_dict()), 400
    
    # Find user
    user = User.query.filter_by(email=email.lower().strip()).first()
    
    if not user or not user.check_password(password):
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Invalid email or password',
            details={}
        ).to_dict()), 401
    
    # Generate tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'token': access_token,
        'refreshToken': refresh_token,
        'user': {
            'id': str(user.id),
            'email': user.email
        }
    }), 200


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user profile.
    
    Headers:
        Authorization: Bearer token
    
    Response:
        User profile information
    """
    user_id = get_jwt_identity()
    
    try:
        user = User.query.get(user_id)
    except Exception:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='User not found',
            details={}
        ).to_dict()), 404
    
    if not user:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='User not found',
            details={}
        ).to_dict()), 404
    
    return jsonify({
        'id': str(user.id),
        'email': user.email,
        'createdAt': user.created_at.isoformat() if user.created_at else None
    }), 200


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint.
    
    Headers:
        Authorization: Bearer token
    
    Response:
        Success message
    """
    # In a more complete implementation, we would invalidate the token
    # For JWT, this is typically done by adding to a blocklist
    
    return jsonify({
        'message': 'Successfully logged out'
    }), 200


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token endpoint.
    
    Headers:
        Authorization: Bearer refresh_token
    
    Response:
        New access token
    """
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    
    return jsonify({
        'token': access_token
    }), 200