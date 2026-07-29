"""
Routes package for DeceptiScan API.
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Import routes to register them with the blueprint
from app.routes import analysis, auth, history, feedback

__all__ = ['api_bp']