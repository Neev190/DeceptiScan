---
name: backend-dev
description: Develop and maintain the Flask/Python backend API, including routes, models, services, and validation logic.
---

## Backend Development — DeceptiScan

### Stack
- Flask 3.0 (app factory pattern), SQLAlchemy, Flask-JWT-Extended
- PostgreSQL 15, Redis 7
- Pydantic for validation

### Project Layout
```
backend/
├── app/
│   ├── __init__.py          # create_app() factory, extensions init
│   ├── validators.py        # Input validation utilities
│   └── routes/
│       ├── __init__.py      # Blueprint registration (api_bp, prefix /api/v1)
│       ├── analysis.py      # POST/GET/DELETE /analyze
│       ├── auth.py          # POST register/login/logout, GET /me
│       ├── feedback.py      # POST /feedback
│       └── history.py       # GET /history (paginated), GET/DELETE by id
├── models/
│   ├── analysis.py          # AnalysisRecord model
│   ├── cache.py             # CachedAnalysis model
│   ├── feedback.py          # UserFeedback model
│   └── user.py              # User model
├── services/
│   ├── cache.py             # Redis cache service
│   └── ml_service.py        # Mock ML service (DistilBERT placeholder)
├── tests/                   # Pytest test files
├── migrations/              # Alembic DB migrations
├── requirements.txt
└── Dockerfile
```

### Conventions
- Error format: `{ "error": { "code": "...", "message": "...", "details": {...} } }`
- Error codes: `INVALID_INPUT`, `ANALYSIS_FAILED`, `RATE_LIMITED`, `NOT_FOUND`, `UNAUTHORIZED`, `INTERNAL_ERROR`
- Auth via JWT bearer token in `Authorization` header
- Rate limiting: 10/min anonymous, 60/min authenticated (Redis-backed)
- Cache key: SHA256 hash of input text
- ML service retry: exponential backoff, max 3 attempts
- `MAX_CONTENT_LENGTH` = 50,000 chars
- No docstrings on trivial code — keep code self-documenting

### Common Tasks

**Add a new endpoint:**
1. Create route function in the appropriate `app/routes/*.py` file
2. Add request validation in `app/validators.py`
3. Implement business logic in `services/`
4. Add model if new DB table needed
5. Create Alembic migration
6. Add tests in `tests/`

**Run the backend:**
```bash
cd backend && flask run --host=0.0.0.0
```

**Run tests:**
```bash
cd backend && python -m pytest tests/ -v
```
