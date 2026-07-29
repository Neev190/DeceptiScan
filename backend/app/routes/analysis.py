"""
Analysis API endpoints for DeceptiScan.
"""
import logging
import time
import uuid
from datetime import datetime
from flask import request, jsonify
from app.routes import api_bp
from app.validators import validate_analyze_request, ValidationError
from services import get_cache_service
from app import db
from models.analysis import AnalysisRecord

logger = logging.getLogger(__name__)


@api_bp.route('/analyze', methods=['POST'])
def analyze_text():
    """
    Analyze text for misinformation.
    
    Request Body:
        content (str): Article text (required, 1-50,000 chars)
        sourceUrl (str): Source URL (optional, must be valid URL format)
        title (str): Article title (optional, max 500 chars)
    
    Response:
        Analysis result with authenticity score and sentence-level analysis
    """
    # Get request data
    data = request.get_json()
    
    # Validate input
    is_valid, error = validate_analyze_request(data)
    if not is_valid:
        return jsonify(error.to_dict()), 400
    
    content = (data.get('content') or data.get('text')).strip()
    source_url = data.get('sourceUrl') or data.get('url')
    if source_url:
        source_url = source_url.strip()
    title = data.get('title')
    if title:
        title = title.strip()
    
    # Get cache service
    cache_service = get_cache_service()
    
    # Compute content hash for caching
    content_hash = cache_service.compute_content_hash(content)
    
    # Check cache first
    cached_result = cache_service.get_analysis(content_hash)
    if cached_result:
        cached_result['is_cached'] = True
        return jsonify(cached_result), 200
    
    # Start timing
    start_time = time.time()
    
    # Perform analysis (mock for now - will integrate ML service later)
    # This is where the ML service would be called
    analysis_result = _perform_analysis(content)
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000  # in milliseconds
    
    # Prepare response
    response = {
        'id': str(uuid.uuid4()),
        'authenticityScore': analysis_result['authenticity_score'],
        'confidence': analysis_result['confidence'],
        'classification': analysis_result['classification'],
        'sentenceAnalysis': analysis_result['sentence_analysis'],
        'processingTime': round(processing_time, 2),
        'analyzedAt': datetime.utcnow().isoformat() + 'Z',
        'modelVersion': '1.0.0',
        'is_cached': False
    }
    
    # Cache the result
    cache_service.set_analysis(content_hash, response)
    
    # Save to database
    try:
        record = AnalysisRecord(
            input_text=content,
            source_url=source_url,
            title=title,
            authenticity_score=analysis_result['authenticity_score'],
            confidence=analysis_result['confidence'],
            classification=analysis_result['classification'],
            sentence_results=analysis_result['sentence_analysis'],
            processing_time=processing_time,
            model_version='1.0.0'
        )
        db.session.add(record)
        db.session.commit()
        response['id'] = str(record.id)
    except Exception as e:
        # Log error but don't fail the request
        db.session.rollback()
        print(f"Database error: {e}")
    
    return jsonify(response), 200


@api_bp.route('/analyze/<analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """
    Retrieve a previous analysis by ID.
    
    Parameters:
        analysis_id: UUID of the analysis record
        
    Response:
        Analysis result if found, error otherwise
    """
    try:
        record = AnalysisRecord.query.get(analysis_id)
    except Exception:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='Analysis not found',
            details={'analysisId': analysis_id}
        ).to_dict()), 404
    
    if not record:
        return jsonify(ValidationError(
            code='NOT_FOUND',
            message='Analysis not found',
            details={'analysisId': analysis_id}
        ).to_dict()), 404
    
    return jsonify(record.to_dict()), 200


def _perform_analysis(text: str) -> dict:
    """
    Perform ML analysis on text using the ML service.
    
    Uses the ML service for classification when available,
    falls back to heuristic analysis if model fails to load.
    """
    from services.ml_service import get_ml_service, MLService
    
    ml_service = get_ml_service()
    
    # Check if model is loaded, try to load if not
    if not ml_service.is_loaded:
        model_loaded = ml_service.load_model()
        if not model_loaded:
            # Fall back to heuristic analysis if model fails to load
            logger.warning("ML model not available, using heuristic analysis")
            return _heuristic_analysis(text)
    
    try:
        # Use ML service for analysis
        result = ml_service.analyze(text)
        
        # Convert to response format
        return {
            'authenticity_score': result.authenticity_score,
            'confidence': result.confidence,
            'classification': result.classification,
            'sentence_analysis': [
                {
                    'index': sa.index,
                    'text': sa.text,
                    'isSuspicious': sa.is_suspicious,
                    'score': sa.score,
                    'confidence': sa.confidence,
                    'category': sa.category,
                    'flags': sa.flags,
                    'explanation': sa.explanation
                }
                for sa in result.sentence_analysis
            ],
            'model_version': result.model_version,
            'processing_time_ms': result.processing_time_ms
        }
    except Exception as e:
        logger.error(f"ML service error: {e}")
        # Fall back to heuristic analysis on error
        return _heuristic_analysis(text)


def _heuristic_analysis(text: str) -> dict:
    """
    Fallback heuristic-based analysis when ML model is unavailable.
    
    Uses pattern matching and heuristics to estimate reliability.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Using heuristic analysis fallback")
    
    # Split text into sentences
    sentences = _split_into_sentences(text)
    
    sentence_analysis = []
    
    for i, sentence in enumerate(sentences):
        # Simple heuristic: analyze based on language patterns
        word_count = len(sentence.split())
        sentence_lower = sentence.lower()
        
        # Check for various indicators
        has_claim = any(word in sentence_lower for word in 
                       ['said', 'according to', 'report', 'study', 'claim', 'announced'])
        
        has_sensationalism = any(word in sentence_lower for word in [
            'shocking', 'unbelievable', 'breaking', 'exposed', 'revealed', 'secret', 'scandal'
        ])
        
        has_loaded = any(word in sentence_lower for word in [
            'evil', 'disgusting', 'horrible', 'terrible', 'amazing', 'incredible', 'outrageous'
        ])
        
        # Generate classification based on heuristics
        if word_count < 10 and not has_claim and not has_sensationalism:
            score = 70 + (25 * (1 - i / max(len(sentences), 1)))
            is_suspicious = score < 75
        elif has_claim:
            score = 30 + (30 * (i % 3))
            is_suspicious = True
        elif has_sensationalism or has_loaded:
            score = 25 + (20 * (i % 3))
            is_suspicious = True
        else:
            score = 40 + (40 * (i % 2))
            is_suspicious = score < 60
        
        # Determine flags
        flags = []
        if has_sensationalism:
            flags.append('sensationalism')
        if has_loaded:
            flags.append('loaded_language')
        if has_claim:
            flags.append('unverified_claim')
        
        # Determine category
        if has_claim:
            category = 'claim'
        elif any(word in sentence_lower for word in ['percent', '%', 'data', 'statistics', 'study']):
            category = 'factual'
        elif any(word in sentence_lower for word in ['i think', 'i believe', 'in my opinion']):
            category = 'opinion'
        else:
            category = 'context'
        
        sentence_analysis.append({
            'index': i,
            'text': sentence,
            'isSuspicious': is_suspicious,
            'score': score,
            'confidence': 0.6 + (0.2 * (i % 2)),
            'category': category,
            'flags': flags,
            'explanation': 'This sentence appears to be ' + 
                          ('reliable' if not is_suspicious else 'potentially unreliable') +
                          ' based on language patterns.'
        })
    
    # Calculate overall score
    total_score = sum(s['score'] for s in sentence_analysis)
    avg_score = total_score / len(sentences) if sentences else 50
    authenticity_score = round(avg_score, 1)
    confidence = 0.65
    
    # Determine classification based on score
    if confidence < 0.3:
        classification = 'unknown'
    elif authenticity_score >= 75:
        classification = 'reliable'
    elif authenticity_score >= 40:
        classification = 'mixed'
    else:
        classification = 'unreliable'
    
    return {
        'authenticity_score': authenticity_score,
        'confidence': confidence,
        'classification': classification,
        'sentence_analysis': sentence_analysis,
        'model_version': 'heuristic-1.0.0',
        'processing_time_ms': 0
    }


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    import re
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter out empty sentences
    return [s.strip() for s in sentences if s.strip()]