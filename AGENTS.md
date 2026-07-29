# DeceptiScan — Project Overview for AI Agents

## Project Summary

DeceptiScan is a web-based misinformation detection tool using NLP (DistilBERT) to analyze news content. It provides sentence-level flagging of suspicious claims and an overall authenticity score (0–100). The project follows a **design-first** workflow — specs live in `.kiro/specs/deceptiscan/`.

## Quick Start

```bash
# Backend (Python/Flask)
cd backend && pip install -r requirements.txt && flask run

# Frontend (React/TypeScript)
cd frontend && npm install && npm run dev

# Full stack (Docker)
docker compose up
```

## Architecture

| Layer | Tech | Location |
|---|---|---|
| Frontend | React 18, TypeScript, Vite | `frontend/` |
| Backend API | Flask 3.0, SQLAlchemy | `backend/` |
| ML Service | DistilBERT (mock for dev) | `backend/services/ml_service.py` |
| Database | PostgreSQL 15 | via `docker-compose.yml` |
| Cache | Redis 7 | via `docker-compose.yml` |
| Proxy | Nginx | `nginx.conf` |

## Key Commands

| Action | Command |
|---|---|
| Backend dev server | `cd backend && flask run --host=0.0.0.0` |
| Backend tests | `cd backend && python -m pytest tests/ -v` |
| Property tests | `cd backend && python -m pytest tests/ -v --hypothesis-show-statistics` |
| Frontend dev server | `cd frontend && npm run dev` |
| Frontend tests | `cd frontend && npm test` |
| Frontend lint | `cd frontend && npm run lint` |
| Docker full stack | `docker compose up --build` |
| DB migration | `cd backend && flask db upgrade` |

## Code Conventions

### Backend (Python/Flask)
- **App factory**: `backend/app/__init__.py` — `create_app()` function
- **Blueprints**: registered in `backend/app/routes/__init__.py` under `/api/v1`
- **Models**: SQLAlchemy models in `backend/models/`
- **Services**: business logic in `backend/services/`
- **Validation**: `backend/app/validators.py`
- **Error format**: `{ "error": { "code": "...", "message": "...", "details": {...} } }`
- **No docstrings or comments on trivial code** — keep code self-documenting

### Frontend (React/TypeScript)
- **Strict TypeScript** (`tsconfig.json`)
- **Components** in `frontend/src/components/` — named exports via `index.ts`
- **Pages** in `frontend/src/pages/`
- **Types** in `frontend/src/types/index.ts`
- **API client** singleton: `frontend/src/services/api.ts`
- **No inline comments** — keep code clean and readable

### API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/analyze` | Optional | Submit text for analysis |
| GET | `/api/v1/analyze/{id}` | Owner | Retrieve analysis |
| DELETE | `/api/v1/analyze/{id}` | Required | Delete analysis |
| POST | `/api/v1/auth/register` | No | Register user |
| POST | `/api/v1/auth/login` | No | Login |
| POST | `/api/v1/auth/logout` | Required | Logout |
| GET | `/api/v1/auth/me` | Required | Current user |
| GET | `/api/v1/history` | Required | Analysis history (paginated) |
| POST | `/api/v1/feedback` | No | Submit feedback |
| GET | `/api/v1/health` | No | Health check |

## Spec Files (.kiro)

The `.kiro/specs/deceptiscan/` directory contains the complete design blueprint:

| File | Purpose |
|---|---|
| `.config.kiro` | Spec metadata (UUID, workflow type) |
| `requirements.md` | 13 functional + non-functional requirements |
| `design.md` | Architecture, data models, API spec, 10 correctness properties |
| `tasks.md` | 27 implementation tasks with dependency graph |

## Task Progress (from tasks.md)

- **17/27 completed**: Infrastructure, DB, Flask core, auth, history, feedback, rate limiting, caching, health check, React setup, ArticleInput, ScoreMeter
- **10 remaining**: ML service core, low confidence handling, ML retry logic, AnalysisResult UI, auth UI, history page, all tests (unit, property, frontend, integration), production config, deployment scripts, recency-based verification routing

## Key Design Decisions

- Classification thresholds: reliable ≥75, mixed 40–74, unreliable <40
- Low confidence: `unknown` when ML confidence < 0.3
- Rate limits: 10/min anonymous, 60/min authenticated
- Cache key: SHA256 hash of input text
- ML retry: exponential backoff, max 3 attempts
- JWT access token: 1 hour expiry; refresh token: 24 hours
