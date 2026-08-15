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
        User profile information with analyses count and avatarUrl
    """
    user_id = get_jwt_identity()
    from app.routes.helpers import find_by_id
    user = find_by_id(User, user_id)
    
    if not user:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='User not found',
            details={}
        ).to_dict()), 404
    
    analyses_count = len(user.analyses) if user.analyses else 0

    return jsonify({
        'id': str(user.id),
        'email': user.email,
        'username': user.username,
        'avatarUrl': user.avatar_url,
        'isAdmin': user.is_admin,
        'createdAt': user.created_at.isoformat() if user.created_at else None,
        'analysesCount': analyses_count
    }), 200


@api_bp.route('/auth/me', methods=['PATCH'])
@jwt_required()
def update_current_user():
    """
    Update current user profile (username).
    
    Headers:
        Authorization: Bearer token
    Request Body:
        username (str, optional): Max 100 chars
    
    Response:
        Updated user profile
    """
    user_id = get_jwt_identity()
    from app.routes.helpers import find_by_id
    user = find_by_id(User, user_id)
    
    if not user:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='User not found',
            details={}
        ).to_dict()), 404
    
    data = request.get_json() or {}
    if 'username' in data:
        username = data.get('username')
        if username is not None:
            # Reject non-string types — blind str() coercion would silently store
            # True as "True", 123 as "123", etc., which is unintended.
            if not isinstance(username, str):
                return jsonify(ValidationError(
                    code='INVALID_INPUT',
                    message='Username must be a string',
                    details={'field': 'username'}
                ).to_dict()), 400
            username = username.strip()
            if len(username) > 100:
                return jsonify(ValidationError(
                    code='INVALID_INPUT',
                    message='Username must not exceed 100 characters',
                    details={'field': 'username'}
                ).to_dict()), 400
            
            # Check for uniqueness against other users
            if username:
                existing_user = User.query.filter(
                    User.username.ilike(username),
                    User.id != user.id
                ).first()
                if existing_user:
                    return jsonify(ValidationError(
                        code='INVALID_INPUT',
                        message='Codename is already registered to another investigator',
                        details={'field': 'username'}
                    ).to_dict()), 400

            user.username = username if username else None

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(ValidationError(
            code='INTERNAL_ERROR',
            message='Failed to update profile',
            details={}
        ).to_dict()), 500

    analyses_count = len(user.analyses) if user.analyses else 0

    return jsonify({
        'id': str(user.id),
        'email': user.email,
        'username': user.username,
        'avatarUrl': user.avatar_url,
        'isAdmin': user.is_admin,
        'createdAt': user.created_at.isoformat() if user.created_at else None,
        'analysesCount': analyses_count
    }), 200


@api_bp.route('/auth/me/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """
    Upload and update current user's profile avatar via Cloudinary.
    
    Headers:
        Authorization: Bearer token
    Form Data:
        file (or avatar): Image file (PNG, JPEG, WEBP, GIF; max 5MB)
        
    Response:
        Updated user profile with new avatarUrl
    """
    import os
    import time
    import logging
    logger = logging.getLogger(__name__)

    user_id = get_jwt_identity()
    from app.routes.helpers import find_by_id
    user = find_by_id(User, user_id)
    
    if not user:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='User not found',
            details={}
        ).to_dict()), 404

    # Extract uploaded file
    file = request.files.get('file') or request.files.get('avatar') or request.files.get('image')
    if not file or not file.filename:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='No image file provided. Please select an image file to upload.',
            details={'field': 'file'}
        ).to_dict()), 400

    # Validate file extension
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'image/pjpeg', 'image/webp', 'image/gif'}
    
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Invalid file format. Allowed formats: PNG, JPEG, WEBP, GIF.',
            details={'field': 'file', 'allowedExtensions': list(ALLOWED_EXTENSIONS)}
        ).to_dict()), 400

    if file.mimetype and file.mimetype.lower() not in ALLOWED_MIMETYPES:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Invalid MIME type. Please upload a valid image file.',
            details={'field': 'file', 'allowedMimeTypes': list(ALLOWED_MIMETYPES)}
        ).to_dict()), 400

    # Validate file size (max 5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    try:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
    except Exception:
        file_size = 0

    if file_size > MAX_FILE_SIZE:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message=f'File size ({round(file_size / (1024*1024), 2)}MB) exceeds the 5MB limit.',
            details={'field': 'file', 'maxSize': '5MB', 'actualSize': file_size}
        ).to_dict()), 400

    if file_size == 0:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Uploaded file is empty.',
            details={'field': 'file'}
        ).to_dict()), 400

    # Check Cloudinary configuration
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')

    if not (cloud_name and api_key and api_secret) or cloud_name == 'your-cloud-name':
        logger.error("Cloudinary credentials are not configured in environment")
        return jsonify(ValidationError(
            code='CONFIG_ERROR',
            message='Profile picture storage is not configured on the server.',
            details={}
        ).to_dict()), 503

    # Upload to Cloudinary
    try:
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )

        upload_result = cloudinary.uploader.upload(
            file,
            folder="deceptiscan/avatars",
            public_id=f"avatar_{str(user.id)}_{int(time.time())}",
            overwrite=True,
            resource_type="image",
            transformation=[
                {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'}
            ]
        )
        
        secure_url = upload_result.get('secure_url') or upload_result.get('url')
        if not secure_url:
            raise ValueError("Cloudinary upload did not return a valid URL")

        # Delete previous avatar from Cloudinary if one exists (non-fatal)
        old_avatar_url = user.avatar_url
        if old_avatar_url and 'cloudinary.com' in old_avatar_url:
            try:
                parts = old_avatar_url.split('/upload/')
                if len(parts) > 1:
                    path_after_upload = parts[1]
                    segments = path_after_upload.split('/', 1)
                    if segments[0].startswith('v') and segments[0][1:].isdigit():
                        raw_path = segments[1] if len(segments) > 1 else segments[0]
                    else:
                        raw_path = path_after_upload
                    old_public_id = raw_path.rsplit('.', 1)[0]
                    cloudinary.uploader.destroy(old_public_id, invalidate=True)
                    logger.info(f"Deleted previous avatar from Cloudinary: {old_public_id}")
            except Exception as destroy_err:
                logger.warning(f"Failed to delete old avatar {old_avatar_url} from Cloudinary (non-fatal): {destroy_err}")

        # Save to database
        user.avatar_url = secure_url
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        logger.error(f"Cloudinary avatar upload failed: {exc}", exc_info=True)
        return jsonify(ValidationError(
            code='UPLOAD_FAILED',
            message='Failed to upload avatar image to storage. Please try again.',
            details={'reason': str(exc)}
        ).to_dict()), 502

    analyses_count = len(user.analyses) if user.analyses else 0

    return jsonify({
        'id': str(user.id),
        'email': user.email,
        'username': user.username,
        'avatarUrl': user.avatar_url,
        'isAdmin': user.is_admin,
        'createdAt': user.created_at.isoformat() if user.created_at else None,
        'analysesCount': analyses_count,
        'message': 'Avatar updated successfully'
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