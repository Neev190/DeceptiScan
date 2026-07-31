"""
History API endpoints for DeceptiScan.
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes import api_bp
from app.validators import ValidationError
from app import db
from models.analysis import AnalysisRecord
import uuid


@api_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """
    Get user's analysis history.
    
    Query Parameters:
        page (int): Page number (default: 1)
        limit (int): Items per page (default: 20, max: 100)
        sort (str): Sort order (default: 'created_at')
    
    Headers:
        Authorization: Bearer token
    
    Response:
        Paginated list of analysis results
    """
    user_id = get_jwt_identity()
    
    # Parse query parameters
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
    except ValueError:
        return jsonify(ValidationError(
            code='INVALID_INPUT',
            message='Page and limit must be integers',
            details={}
        ).to_dict()), 400
    
    # Validate limits
    page = max(1, page)
    limit = min(max(1, limit), 100)
    
    # Query history
    try:
        query = AnalysisRecord.query.filter_by(user_id=uuid.UUID(user_id))
        query = query.order_by(AnalysisRecord.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        records = pagination.items
    except Exception as e:
        return jsonify(ValidationError(
            code='INTERNAL_ERROR',
            message='Failed to retrieve history',
            details={'error': str(e)}
        ).to_dict()), 500
    
    items = [record.to_dict() for record in records]
    return jsonify({
        'items': items,
        'data': items,
        'page': page,
        'limit': limit,
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@api_bp.route('/history/<analysis_id>', methods=['GET'])
@jwt_required()
def get_history_item(analysis_id):
    """
    Get a specific analysis from history.
    
    Parameters:
        analysis_id: UUID of the analysis
    
    Headers:
        Authorization: Bearer token
    
    Response:
        Analysis details if found and owned by user
    """
    user_id = get_jwt_identity()
    
    from app.routes.helpers import find_by_id
    record = find_by_id(AnalysisRecord, analysis_id)
    
    if not record:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='Analysis not found',
            details={'analysisId': analysis_id}
        ).to_dict()), 404
    
    # Check ownership
    if str(record.user_id) != user_id:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='Analysis not found',
            details={'analysisId': analysis_id}
        ).to_dict()), 404
    
    return jsonify(record.to_dict()), 200


@api_bp.route('/history/<analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_history_item(analysis_id):
    """
    Delete an analysis from history.
    
    Parameters:
        analysis_id: UUID of the analysis
    
    Headers:
        Authorization: Bearer token
    
    Response:
        Success message if deleted
    """
    user_id = get_jwt_identity()
    
    from app.routes.helpers import find_by_id
    record = find_by_id(AnalysisRecord, analysis_id)
    
    if not record:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='Analysis not found',
            details={'analysisId': analysis_id}
        ).to_dict()), 404
    
    # Check ownership
    if str(record.user_id) != user_id:
        return jsonify(ValidationError(
            code='UNAUTHORIZED',
            message='You do not have permission to delete this analysis',
            details={}
        ).to_dict()), 403
    
    try:
        db.session.delete(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(ValidationError(
            code='INTERNAL_ERROR',
            message='Failed to delete analysis',
            details={'error': str(e)}
        ).to_dict()), 500
    
    return jsonify({
        'message': 'Analysis deleted successfully'
    }), 200