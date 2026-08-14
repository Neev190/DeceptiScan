# DeceptiScan Architecture

## System Overview

DeceptiScan is a web-based misinformation detection tool that analyzes text content using machine learning to provide authenticity scores and sentence-level analysis. The system follows a multi-tier architecture with React frontend, Flask API backend, ML service layer, and hosted PostgreSQL database with pgvector for similarity search.

## Technology Stack

### Backend
- **Flask 3.0.0** - Web framework
- **Flask-SQLAlchemy 3.1.1** - ORM and database management  
- **Flask-JWT-Extended 4.6.0** - JWT authentication
- **Flask-CORS 4.0.0** - Cross-origin resource sharing
- **Flask-Migrate 4.0.7** - Database migrations via Alembic 1.13.0
- **PostgreSQL (hosted via Neon, pgvector-enabled)** - Primary database with vector similarity search
- **Redis-compatible (hosted via Upstash)** - Caching layer (optional, degrades gracefully)

### Frontend
- **React 18.2.0** - UI framework
- **TypeScript 5.3.0** - Type safety
- **Vite 5.0.0** - Build tool and dev server
- **React Router DOM 6.20.0** - Client-side routing
- **Axios 1.6.0** - HTTP client
- **Tailwind CSS 3.4.19** - Styling framework

### Machine Learning
- **DistilBERT** - Fine-tuned transformer model for text classification
- **PyTorch 2.2.0+** - ML framework
- **Transformers 4.36.2+** - Hugging Face model library
- **Sentence-Transformers 2.7.0+** - Embedding generation for retrieval
- **LIAR Dataset** - Training corpus for fact-checking

### Infrastructure  
- **Docker Compose** - Container orchestration (present but unused - see Deployment Architecture)
- **Nginx** - Reverse proxy configuration (present but unused)
- **Gunicorn 21.2.0** - WSGI HTTP server for production
- **Neon** - Hosted PostgreSQL service (live environment)
- **Upstash** - Hosted Redis service (live environment)

## Architecture Layers

### 1. Presentation Layer (Frontend)
```
React App (Port 3000)
├── Components/
│   ├── ArticleInput - Text submission form
│   ├── ScoreMeter - Authenticity score visualization  
│   ├── AnalysisResult - Sentence-level results display
│   └── AuthForms - Login/registration UI
├── Pages/
│   ├── Home - Main analysis interface
│   ├── History - User analysis history
│   └── Auth - Authentication flows
└── Services/
    └── api.ts - Centralized API client (Axios singleton)
```

### 2. API Layer (Flask Backend)
```
Flask App (Port 5000)
├── /api/v1/analyze [POST] - Text analysis endpoint
├── /api/v1/analyze/{id} [GET] - Retrieve analysis by ID  
├── /api/v1/auth/* - Authentication endpoints
├── /api/v1/history [GET] - User analysis history (paginated)
├── /api/v1/feedback [POST] - User feedback submission
├── /api/v1/retrieve [GET] - Similar claims retrieval
└── /api/v1/health [GET] - System health check
```

### 3. Service Layer
```
Services/
├── MLService - DistilBERT text classification with retry logic
├── RetrievalService - pgvector similarity search against LIAR corpus  
├── RecencyService - Routing logic for recent vs. cached content
└── CacheService - Redis-based result caching (SHA256 content hash keys)
```

### 4. Data Layer
```
PostgreSQL Database
├── users - User accounts and authentication
├── analysis_records - Analysis results and metadata
├── user_feedbacks - User feedback on analysis accuracy
├── cached_analyses - Database-level caching with TTL
└── claim_embeddings - LIAR corpus with vector embeddings (384-dim)
```

## Data Flow Analysis

### /analyze Request Path

1. **Request Reception** (`analysis.py:analyze_text()`)
   - Validate input via `validate_analyze_request()` (1-50k chars, optional URL/title)
   - Extract JWT user identity (optional authentication)

2. **Cache Lookup** (`cache.py`)
   - Compute SHA256 hash of input content
   - Check Redis cache, return if hit with `is_cached: true`

3. **Recency Routing** (`recency_service.py`)
   - Check if content appears time-sensitive for routing decisions
   - Route to ML analysis if not cached and not recent-specific

4. **ML Analysis** (`ml_service.py`)
   - Load DistilBERT model with exponential backoff retry (max 3 attempts)
   - Perform sentence-level classification and overall authenticity scoring
   - Fall back to heuristic analysis if ML service unavailable

5. **Retrieval Enhancement** (`retrieval_service.py`)  
   - Generate sentence-transformer embedding for input text
   - Query `claim_embeddings` table via pgvector cosine similarity
   - Retrieve top-5 similar LIAR dataset claims (non-blocking, degrades gracefully)
   - Sanitize retrieved claim text to prevent prompt injection

6. **Delta Logging** (Background Thread)
   - Re-analyze text with retrieved claims as context
   - Log score deltas >10 points for retrieval impact analysis
   - Thread-safe with separate Flask app context

7. **Response Assembly**
   - Combine ML results, retrieval claims, processing metrics
   - Generate UUID for analysis record
   - Cache result in Redis with TTL

8. **Database Persistence**
   - Save `AnalysisRecord` with user association (if authenticated)
   - Include sentence analysis, retrieved claims, and metadata
   - Rollback-safe error handling

### Authentication Flow

1. **Registration/Login** (`auth.py`)
   - Email/password validation via `validate_auth_request()`
   - Password hashing with bcrypt salting
   - JWT token generation (1hr access + 24hr refresh)

2. **Request Authorization**
   - Optional JWT verification via `@jwt_required(optional=True)`
   - User identity extraction for analysis ownership
   - Graceful degradation for anonymous users

3. **Token Refresh** 
   - Refresh token exchange for new access token
   - Maintains session continuity without re-authentication

## Data Model

### Core Entities

```sql
-- Users table
users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP
);

-- Analysis records  
analysis_records (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    input_text TEXT NOT NULL,
    source_url VARCHAR(2048),
    title VARCHAR(500),
    authenticity_score FLOAT NOT NULL,
    confidence FLOAT NOT NULL, 
    classification VARCHAR(50) NOT NULL, -- reliable/mixed/unreliable/unknown
    sentence_results JSONB NOT NULL DEFAULT '[]',
    processing_time FLOAT, -- milliseconds
    model_version VARCHAR(50),
    is_cached INTEGER DEFAULT 0,
    similar_claims JSONB, -- Retrieved LIAR claims
    created_at TIMESTAMP DEFAULT now()
);

-- User feedback
user_feedbacks (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analysis_records(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    feedback_type VARCHAR(50) NOT NULL, -- helpful/incorrect/disputed
    corrected_classification VARCHAR(50),
    comment TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Vector similarity corpus
claim_embeddings (
    id UUID PRIMARY KEY,
    statement_text TEXT NOT NULL,
    label VARCHAR(20) NOT NULL, -- LIAR dataset labels
    embedding VECTOR(384) NOT NULL, -- sentence-transformer embeddings
    created_at TIMESTAMP DEFAULT now()
);
```

### Key Indexes
- `idx_analysis_user_created` - User history queries
- `idx_analysis_created_at` - Temporal analysis queries  
- `idx_claim_embeddings_embedding` - IVFFlat cosine similarity search
- `ix_users_email` - Authentication lookups

## Caching Strategy

### Multi-Layer Caching
1. **Upstash Redis Cache** (Primary)
   - Key: SHA256 hash of input content
   - Value: Complete analysis result JSON
   - TTL: Configurable (default 3600 seconds)
   - Fails open on unavailability (see SECURITY.md)

2. **Model Caching**
   - DistilBERT model loaded once per process
   - Lazy loading with health checks
   - Graceful degradation to heuristic analysis

**Note**: The `cached_analyses` database table exists in the schema (migration 001_initial) but is not actively used in the current caching implementation. Current caching logic in `cache.py` uses only Redis.

### Cache Invalidation
- Content-based keys ensure consistency
- No explicit invalidation needed (immutable results for same content)
- TTL-based expiration for recency requirements

## Security Architecture

### Authentication & Authorization
- **JWT-based** access control with refresh tokens
- **Optional authentication** - anonymous analysis permitted (rate limiting infrastructure exists but is not currently wired to /analyze; see SECURITY.md)
- **bcrypt password hashing** with per-user salt generation

### Input Validation & Sanitization
- **Content length limits**: 1-50,000 characters
- **URL validation** for source URLs
- **Prompt injection protection** in retrieved claims via regex sanitization
- **SQL injection prevention** via SQLAlchemy parameterized queries

### Data Protection
- **UUID primary keys** prevent enumeration attacks
- **User data isolation** via foreign key constraints
- **Soft deletion** for analysis records (SET NULL on user deletion)
- **CORS configuration** for cross-origin request control

## Deployment Architecture

### Current Infrastructure
**Live Environment**: DeceptiScan uses hosted services rather than self-managed containers:
- **Database**: Neon PostgreSQL (AWS ap-southeast-1) 
- **Cache**: Upstash Redis
- **Application**: Direct Flask execution for development

### Docker Compose Configuration (Unused)
The repository contains `docker-compose.yml` and supporting Docker files for local container orchestration, but this setup is **not actively used** in the current deployment. The configuration exists as alternative deployment option but the live environment uses hosted services.
### Docker Compose Reference (Present but Unused)
The following configuration exists in `docker-compose.yml` but is not the active deployment:

```yaml
Services:
├── postgres (pgvector/pgvector:pg15)
│   ├── Port 5432 exposed
│   ├── Volume: postgres_data persistence
│   └── Health checks: pg_isready
├── redis (redis:7-alpine)  
│   ├── Port 6379 exposed
│   ├── Volume: redis_data persistence
│   └── Health checks: redis-cli ping
├── backend (Flask)
│   ├── Port 5000 exposed
│   ├── Depends on: postgres, redis health
│   └── Volume: ./backend mounted for development
├── frontend (React/Vite)
│   ├── Port 3000 exposed  
│   ├── Depends on: backend
│   └── Volume: ./frontend mounted for development
└── nginx (reverse proxy)
    ├── Ports 80/443 exposed
    ├── Routes: / → frontend, /api/ → backend
    └── Depends on: backend, frontend
```

### Network Architecture
- **Hosted services**: Neon PostgreSQL and Upstash Redis accessed via internet connections
- **Local development**: Direct Flask application (typically port 5000)
- **Production consideration**: Nginx reverse proxy configuration available in `nginx.conf`

### Environment Configuration
- **Current setup**: Direct connection to hosted services via `.env` credentials
- **Database**: Neon connection string with SSL requirement
- **Cache**: Upstash Redis with authentication
- **Connection pooling**: 10 base connections, max 20 overflow, 30s timeout

## Performance Characteristics

### Scalability Considerations
- **Stateless backend**: Horizontal scaling via load balancer
- **Database connection pooling**: 10 base connections, max 20 overflow
- **ML model sharing**: Single model instance per container (memory optimization)
- **Cache hit rate**: Reduces ML computation for duplicate content

### Bottleneck Analysis
- **ML inference**: ~2-5s per analysis (DistilBERT sentence processing)
- **Database queries**: Optimized via composite indexes on common access patterns
- **Vector similarity**: IVFFlat index provides sub-linear search performance
- **Memory usage**: DistilBERT model (~250MB), sentence-transformer (~200MB)

### Monitoring Points
- **Health endpoint**: `/api/v1/health` - Database, cache, and overall status
- **Processing time tracking**: Analysis duration logged per request
- **Cache hit rates**: Redis performance metrics
- **Error rates**: ML service availability and fallback usage

## Known Limitations

### Architectural Constraints
1. **Single-node ML serving**: Model loaded per backend instance, no horizontal scaling of ML component
2. **Synchronous analysis**: Blocking request-response pattern, no async job processing
3. **In-memory model state**: Model reloading required on container restart
4. **Cache dependency**: Performance degradation when Redis unavailable
5. **Vector search limits**: IVFFlat index requires periodic optimization for large datasets

### Data Model Limitations  
1. **Content immutability**: Same text always produces same result (no temporal analysis evolution)
2. **No analysis versioning**: Model updates invalidate comparison with historical results
3. **Limited feedback integration**: User corrections not fed back into ML training pipeline
4. **Retrieval corpus staleness**: LIAR dataset fixed at training time, no real-time claim updates

### Security Considerations
1. **JWT secret rotation**: Manual process, no automated key management
2. **Rate limiting implementation**: Present in `cache.py` but not currently enforced on any routes (see SECURITY.md for detailed analysis)
3. **Content sanitization**: Basic regex patterns, not comprehensive prompt injection defense
4. **Audit logging**: Limited to application logs, no dedicated security event tracking

### Operational Limitations
1. **No CI/CD pipeline**: Manual deployment and testing processes
2. **Single-environment configuration**: No staging/production environment separation in current setup  
3. **Backup strategy**: Relies on hosted service providers (Neon/Upstash) for data persistence and backup
4. **Monitoring gaps**: Application-level health checks only, no comprehensive observability stack
5. **No test/production database isolation**: Tests connect directly to the real Neon production database, confirmed via runtime inspection, no separate TEST_DATABASE_URL configured (see TESTING.md)

## Migration & Evolution

### Database Schema Management
- **Alembic migrations**: Version-controlled schema evolution
- **Current version**: 002_retrieval_corpus (pgvector support)
- **Backward compatibility**: Foreign key constraints preserve data integrity during schema changes

### Model Version Management
- **Version tracking**: `model_version` field in analysis records
- **Upgrade path**: Requires retraining and checkpoint replacement
- **Historical analysis**: Previous results remain valid but not comparable across model versions

### Service Interface Evolution
- **API versioning**: `/api/v1/` prefix allows future version coexistence  
- **Backward compatibility**: New optional fields preserve existing client compatibility
- **Extension points**: Plugin architecture possible for additional analysis services