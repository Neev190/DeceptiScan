"""
Feedback API endpoints for DeceptiScan.
"""
import uuid
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.routes import api_bp
from app.validators import validate_feedback_request, ValidationError
from app import db
from models.feedback import UserFeedback
from models.analysis import AnalysisRecord


@api_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback on an analysis.
    
    Note: This route uses manual JWT handling (no @jwt_required decorator) to ensure
    consistent behavior with /analyze route. Both optional-auth routes should handle
    malformed/expired tokens gracefully by treating them as anonymous requests.
    
    Request Body:
        analysisId (str): ID of the analysis (required)
        feedback (object): Feedback object (required)
            type (str): Type of feedback - "helpful", "incorrect", "disputed" (required)
            comment (str): Optional comment
            correctedClassification (str): If incorrect, the correct classification
    
    Headers:
        Authorization: Bearer token (optional)
    
    Response:
        Feedback ID if successful
    """
    data = request.get_json()
    
    # Validate input
    is_valid, error = validate_feedback_request(data)
    if not is_valid:
        return jsonify(error.to_dict()), 400
    
    analysis_id = data.get('analysisId') or data.get('analysis_id')

    # Validate analysis_id is a well-formed UUID before any DB lookup.
    # A non-UUID string (e.g. path traversal or garbage) must return 404,
    # not a 500 from an unhandled UUID parse error elsewhere in the stack.
    import uuid as _uuid
    try:
        _uuid.UUID(str(analysis_id))
    except (ValueError, AttributeError):
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='Analysis not found',
            details={'analysisId': analysis_id}
        ).to_dict()), 404
    
    # Get user ID if authenticated
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = identity
    except Exception:
        user_id = None
    
    # Verify analysis exists
    from app.routes.helpers import find_by_id
    analysis = find_by_id(AnalysisRecord, analysis_id)
    
    if not analysis:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='Analysis not found',
            details={'analysisId': analysis_id}
        ).to_dict()), 404
    
    # Extract feedback data
    feedback_data = data.get('feedback', {})
    if isinstance(feedback_data, dict):
        feedback_type = feedback_data.get('type')
        comment = feedback_data.get('comment')
        corrected_classification = feedback_data.get('correctedClassification')
    else:
        feedback_type = data.get('type')
        comment = data.get('comment')
        corrected_classification = data.get('correctedClassification')
    
    # Create feedback record
    feedback = UserFeedback(
        id=uuid.uuid4(),
        analysis_id=analysis_id,
        user_id=uuid.UUID(user_id) if user_id else None,
        feedback_type=feedback_type,
        comment=comment,
        corrected_classification=corrected_classification,
        created_at=datetime.utcnow()
    )
    
    try:
        db.session.add(feedback)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(ValidationError(
            code='INTERNAL_ERROR',
            message='Failed to submit feedback',
            details={'error': str(e)}
        ).to_dict()), 500
    
    return jsonify({
        'feedbackId': str(feedback.id),
        'message': 'Feedback submitted successfully'
    }), 201