---
name: docker-infra
description: Manage Docker Compose infrastructure, Nginx configuration, and production deployment for the full stack.
---

## Docker & Infrastructure — DeceptiScan

### Services (docker-compose.yml)

| Service | Image | Port | Health Check |
|---|---|---|---|
| `postgres` | postgres:15-alpine | 5432 | pg_isready |
| `redis` | redis:7-alpine | 6379 | redis-cli ping |
| `backend` | Python 3.11-slim (build) | 5000 | Flask dev server |
| `frontend` | Node 20-alpine (build) | 3000 | Vite dev server |
| `nginx` | nginx:alpine | 80, 443 | — |

### Network
- All services share `deceptiscan-network` bridge network
- Backend connects to DB via `postgres:5432` and Redis via `redis:6379`

### Volumes
- `postgres_data` — persistent database storage
- `redis_data` — persistent cache storage
- `model_cache` — ML model weights cache (backend)

### Nginx (nginx.conf)
- `/` → frontend:3000 (React SPA)
- `/api/` → backend:5000 (Flask API)
- Single `server` block on port 80 (HTTP)

### Environment Variables (required)
Backend (`.env`):
- `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`
- `MAX_CONTENT_LENGTH` (default 50000)

Frontend (`.env`):
- `VITE_API_URL` (http://localhost:5000/api/v1 for dev)

### Common Tasks

**Start full stack:**
```bash
docker compose up --build
```

**Start specific service:**
```bash
docker compose up backend -d
```

**View logs:**
```bash
docker compose logs -f backend
```

**Rebuild and restart:**
```bash
docker compose up --build -d
```

**Reset everything (destroy volumes):**
```bash
docker compose down -v
```

### Production Config (pending)
- Task 25 in `.kiro/specs/deceptiscan/tasks.md`
- HTTPS certs in `./ssl/` volume (placeholder)
- Gunicorn workers instead of Flask dev server
- Static file serving via Nginx
