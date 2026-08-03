"""
DeceptiScan Flask Application
"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_name=None):
    """Application factory for creating Flask app instance."""
    app = Flask(__name__)

    # Load configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    if config_name == 'testing':
        app.config['TESTING'] = True
        db_uri = os.getenv('TEST_DATABASE_URL') or os.getenv('DATABASE_URL') or 'sqlite:///:memory:'
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        if db_uri.startswith('sqlite'):
            from sqlalchemy.pool import StaticPool
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'connect_args': {'check_same_thread': False},
                'poolclass': StaticPool,
            }
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
            'DATABASE_URL',
            'postgresql://deceptiscan:password@localhost:5433/deceptiscan'
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'max_overflow': 20,
            'pool_timeout': 30,
        }
    
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 86400))  # 24 hours
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 50000))
    
    # Redis configuration
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # Initialize cache service (services is at backend root level)
    try:
        from services.cache import init_cache_service
        init_cache_service(app.config['REDIS_URL'])
    except Exception as e:
        print(f"Warning: Could not initialize cache service: {e}")

    # Register blueprints
    try:
        from app.routes import api_bp
        app.register_blueprint(api_bp, url_prefix='/api/v1')
    except Exception as e:
        print(f"Warning: Could not register blueprints: {e}")

    # Health check endpoint
    @app.route('/api/v1/health')
    def health_check():
        from services.cache import get_cache_service
        cache = get_cache_service()
        
        # Check database connectivity
        db_status = 'healthy'
        cache_status = 'healthy'
        
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception:
            db_status = 'unhealthy'
        
        if not cache.health_check():
            cache_status = 'unhealthy'
        
        overall = 'healthy' if db_status == 'healthy' and cache_status == 'healthy' else 'degraded'
        
        return {
            'status': overall,
            'version': '1.0.0',
            'dependencies': {
                'database': db_status,
                'cache': cache_status
            }
        }

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)