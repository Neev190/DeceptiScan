# DeceptiScan

> **A noir-themed, bureau-grade misinformation detection engine pairing fine-tuned DistilBERT classification with pgvector semantic claim retrieval.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15_pgvector-4169E1?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![React](https://img.shields.io/badge/React-18.2_TypeScript-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-245%20Passing-success?style=flat)]()

---

## 📌 Problem Statement

Automated fact-checking tools frequently suffer from two opposing failure modes: opaque single-score outputs that lack granular provenance, or heavy generative LLM pipelines prone to hallucinations, prompt injection, and excessive latency. 

**DeceptiScan** takes a structured, verifiable approach to news verification. Given any article or statement (up to 50,000 characters), the system:
1. Segments content into discrete sentence-level assertions.
2. Evaluates each claim via a fine-tuned **DistilBERT** transformer to produce calibrated reliability probabilities ($0\text{--}100$).
3. Queries an indexed corpus of human-verified statements using **pgvector** cosine similarity ($384$-dimensional `all-MiniLM-L6-v2` embeddings) to ground predictions in historical fact-check data.
4. Renders the output in an investigative **"bureau case file"** UI that breaks down the aggregate score into sentence-level flags (e.g., sensationalism, loaded language, unverified claims) alongside semantically matched prior claims.

---

## 🏛️ System Architecture

```
                                  ┌──────────────────────────────────────────────┐
                                  │      React 18 + TypeScript + Vite Client     │
                                  │   (Noir Bureau Theme / Lenis Smooth Scroll)  │
                                  └──────────────────────┬───────────────────────┘
                                                         │ HTTP / REST (JWT Auth)
                                                         ▼
                                  ┌──────────────────────────────────────────────┐
                                  │           Flask 3.0 API Gateway              │
                                  │  (/api/v1/analyze, /auth, /history, /feedbk) │
                                  └──────┬───────────────┬───────────────┬───────┘
                                         │               │               │
                     ┌───────────────────┘               │               └───────────────────┐
                     ▼                                   ▼                                   ▼
        ┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
        │   Upstash Redis Cache   │         │    ML Inference Engine  │         │   PostgreSQL + pgvector │
        │  SHA-256 Keyed Results  │         │  DistilBERT (LIAR V1)   │         │  (Neon Serverless DB)   │
        │  (Fail-Open Fallback)   │         │  3x Exponential Backoff │         │  claim_embeddings (384d)│
        └─────────────────────────┘         └────────────┬────────────┘         │  analysis_records JSONB │
                                                         │                      └────────────┬────────────┘
                                                         ▼                                   │
                                            ┌─────────────────────────┐                      │
                                            │ Semantic Retrieval Svc  │                      │
                                            │ all-MiniLM-L6-v2 (384d) ├──────────────────────┘
                                            │ Cosine Search (IVFFlat) │  Top-k Similar Claims (>= 0.45)
                                            └────────────┬────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ Non-Blocking Background │
                                            │  Delta-Logging Thread   │
                                            │  (Triggers on >10pt Δ)  │
                                            └─────────────────────────┘
```

### End-to-End Request Pipeline (`POST /api/v1/analyze`)

1. **Input Validation**: Request payload (`content`, optional `title` and `sourceUrl`) is validated against strict Pydantic schemas (1–50,000 chars, URI structure).
2. **SHA-256 Cache Interception**: A deterministic SHA-256 hash of the content is queried in Upstash Redis. Cache hits return immediately with `is_cached: true`.
3. **Recency Routing Check**: The content is evaluated for temporal references (e.g., within 7 days); if active, requests can route to external fact-checking providers.
4. **Sentence Segmentation & DistilBERT Classification**:
   - The article is decomposed into individual sentences.
   - The fine-tuned `distilbert-base-uncased` binary classifier evaluates $P(\text{reliable})$, mapped to an authenticity score from $0$ to $100$:
     - $\ge 75 \implies \text{Reliable}$
     - $40\text{--}74 \implies \text{Mixed}$
     - $< 40 \implies \text{Unreliable}$
     - Low confidence ($< 0.10$ rescaled) $\implies \text{Unknown}$
   - Includes automatic 3-stage exponential backoff retry with deterministic heuristic fallback.
5. **pgvector Semantic Claim Retrieval**:
   - Input text is embedded via `sentence-transformers/all-MiniLM-L6-v2` into a 384-dimensional unit vector.
   - An IVFFlat cosine search (`<=>`) executes against the `claim_embeddings` table.
   - Matches are filtered at an empirical similarity cutoff of $\ge 0.45$ and sanitized against prompt-injection tokens before serialization.
6. **Asynchronous Delta-Logging**: A daemon background thread re-evaluates the classification with retrieved claims appended as context, logging any scoring shift exceeding $10$ points for model observability without adding latency to the response.
7. **Persistence & Response**: The analysis record, sentence breakdown, and similar claims are saved to PostgreSQL (with optional user association if JWT is present) and returned to the client.

---

## 💡 Key Architectural & Engineering Decisions

### 1. pgvector in PostgreSQL vs. Dedicated Vector Databases (Pinecone, Qdrant, Milvus)
- **Unified ACID State**: Housing user records, analysis histories, JSONB sentence metadata, and claim embeddings in a single PostgreSQL instance (via Neon) eliminates cross-system synchronization bugs and distributed transaction overhead.
- **Operational Simplicity & Cost**: At ~8,200 indexed claims with 384-dimensional vectors, an IVFFlat index (`lists = 100`) executes similarity searches in sub-10ms timeframes without requiring external network hops to third-party vector SaaS providers.

### 2. Fine-Tuned DistilBERT vs. Large Generative LLMs (e.g., GPT-4, LLaMA-3)
- **Determinism & Speed**: DistilBERT preserves 97% of BERT’s language comprehension with 40% fewer parameters, running CPU inference in ~2–5 seconds per article (~250MB memory footprint).
- **Zero Hallucination Surface**: A discriminative classifier trained with cross-entropy loss outputs calibrated class probabilities rather than freeform text, eliminating the risk of synthetic fabrications or prompt-injection jailbreaks.
- **Cost**: Eliminates per-token API costs for high-throughput batch evaluation.

### 3. Fail-Open Architecture for Caching & Rate Limiting
- **Resilience Over Enforcement**: If the Upstash Redis instance experiences a network partition or outage, the `CacheService` catches `redis.RedisError` and silently fails open (treating cache misses as fresh requests and granting rate-limit allowances).
- **Availability Guarantee**: Redis is treated as a performance accelerator, never a hard availability dependency that could bring down the core analysis API.

---

## 📊 Verified Metrics & Benchmark Data

All metrics below are drawn directly from codebase evaluation logs (`backend/ml_models/metrics.json`, `backend/ml_models/RETRIEVAL_CARD.md`, and the automated test suite).

### 1. DistilBERT Misinformation Classifier (LIAR Test Split)
Evaluated on the held-out test split of the benchmark **LIAR dataset** (Wang, 2017) using binary label mapping (`reliable`: *true, mostly-true*; `unreliable`: *pants-fire, false, barely-true*; ambiguous *half-true* instances dropped).

| Metric | Measured Value | Baseline / Context |
|---|---|---|
| **Test Accuracy** | **64.57%** (0.6457) | 54.72% (Majority Class Baseline) |
| **Macro Precision** | **64.18%** (0.6418) | Balanced across classes |
| **Macro Recall** | **63.78%** (0.6378) | Balanced across classes |
| **Macro F1-Score** | **63.82%** (0.6382) | Verified in `metrics.json` |
| **Test Loss** | **0.6241** | Cross-entropy loss |
| **Training Setup** | 1 Epoch, lr=2e-5, batch=32, max_len=64 tokens, seed=42 |

#### Test Split Confusion Matrix
```
                    Predicted
                Unreliable  Reliable
Actual Unreliable    401        155
Actual Reliable      205        255
```
*Note on Accuracy Ceiling*: 64.57% test accuracy represents the documented performance ceiling in academic literature for statement-only classification on the LIAR dataset without access to external speaker metadata or source party affiliations.

### 2. Semantic Retrieval Calibration (pgvector + all-MiniLM-L6-v2)
Evaluated across 51 top-3 retrieval queries from 20 held-out test statements against the ~8,200 training corpus:

| Percentile / Metric | Cosine Similarity Score | Empirical Interpretation |
|---|---|---|
| **Max Match** | **0.9833** | Near-identical / verbatim statement rewrites |
| **P90** | **0.7922** | Top 10% highest-confidence topical matches |
| **P75** | **0.7009** | Strongly related subject claims (e.g. tax/jobs data) |
| **Mean** | **0.6133** | Average retrieved semantic neighbor |
| **P50 (Median)** | **0.5649** | Moderate contextual relevance |
| **Threshold Cutoff** | **0.4500** | Empirically filters out nearest-neighbor noise |

### 3. Offline Adversarial & Sensitivity Testing
*(Note: Distinct from the live-traffic delta-logging thread, these metrics were generated via offline adversarial pair testing)*
- **Mean Score Delta**: `-2.48 points` across matched adversarial statement pairs (e.g. politically coded vs neutral wording).
- **Maximum Absolute Delta**: `3.7 points` (well within the 15-point stability envelope).
- **Model Determinism**: Control group standard deviation is `0.0` (fully deterministic inference).

### 4. Automated Test Suite
- **Backend (Pytest + Hypothesis)**: **245 tests passing** covering JWT auth edge cases, stored XSS neutralization, property-based invariants, rate limiting, and end-to-end integration.
- **Frontend (Vitest + Testing Library)**: Component, score meter, and page navigation test coverage.

---

## 🛠️ Complete Tech Stack

| Layer | Technologies | Role in System |
|---|---|---|
| **Frontend UI** | React 18, TypeScript 5.3, Vite 5, Tailwind CSS 3.4, Lenis | Responsive noir detective bureau interface, live authenticity meter, claim inspector |
| **Backend API** | Python 3.11, Flask 3.0, Flask-JWT-Extended 4.6, Pydantic 2.5 | RESTful API endpoints, request validation, authentication, and error handling |
| **ML & NLP** | PyTorch 2.2+, Transformers 4.36+, DistilBERT, Sentence-Transformers 2.7+ | Sentence-level misinformation scoring & 384-dimensional vector embedding generation |
| **Database** | PostgreSQL 15 (hosted on Neon) + `pgvector` extension | Relational storage for users/analyses and vector similarity search for claim retrieval |
| **Caching** | Redis 7 (hosted via Upstash) | SHA-256 content-hash result caching and rate-limit tracking |
| **Security** | bcrypt 4.1, python-jose, Regex injection sanitizers | Salted password hashing, JWT signing, input validation, and XSS filtering |
| **Testing** | Pytest, Hypothesis (property testing), Vitest, Playwright | Backend property/security tests, frontend component and integration tests |

---

## 🔌 API Endpoint Reference

All endpoints are versioned under `/api/v1`:

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/v1/analyze` | Optional (Bearer JWT) | Analyze article text (1–50k chars); returns score, sentence flags, and similar claims |
| `GET` | `/api/v1/analyze/<id>` | Public | Retrieve a previous analysis record by UUID |
| `GET` | `/api/v1/retrieve` | Public | Vector similarity search over the claim corpus (`?query=...`) |
| `POST` | `/api/v1/auth/register` | No | Register new investigator account (returns 1h access & 24h refresh JWTs) |
| `POST` | `/api/v1/auth/login` | No | Authenticate user credentials and return JWT pair |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT | Generate new access token from valid refresh token |
| `GET` | `/api/v1/auth/me` | Access JWT | Retrieve authenticated user profile and analysis tally |
| `PATCH` | `/api/v1/auth/me` | Access JWT | Update investigator codename / username |
| `POST` | `/api/v1/auth/logout` | Access JWT | Invalidate active session |
| `GET` | `/api/v1/history` | Access JWT | Fetch paginated analysis history for the current user |
| `GET` | `/api/v1/analyses/recent` | Access JWT | Fetch user's N most recent analyses (default 5, max 20) |
| `GET` | `/api/v1/history/<id>` | Access JWT | Retrieve specific historical analysis (with ownership verification) |
| `DELETE` | `/api/v1/history/<id>` | Access JWT | Delete an analysis record belonging to the user |
| `POST` | `/api/v1/feedback` | Optional | Submit user feedback (`helpful`, `incorrect`, `disputed`) on an analysis |
| `GET` | `/api/v1/health` | No | Health check returning status of database and cache connections |

---

## 🚀 Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL with `pgvector` extension (or a free [Neon](https://neon.tech) PostgreSQL instance)
- Redis instance (or a free [Upstash](https://upstash.com) Redis instance)

### 1. Repository Clone & Environment Setup
```bash
git clone https://github.com/Neev190/DeceptiScan.git
cd DeceptiScan
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (.env)
cp .env.example .env
# Edit .env with your DATABASE_URL (with pgvector enabled), REDIS_URL, and JWT_SECRET_KEY
```

> **Note on Model Checkpoint**: The fine-tuned DistilBERT model automatically downloads from Hugging Face (`Yakuza190/deceptiscan-distilbert-liar`) on first run. No manual training step is required.

```bash
# Run database migrations
flask db upgrade

# (Optional) Populate the ~8,200 LIAR claim embeddings for pgvector retrieval
python ml_training/build_retrieval_corpus.py

# Start Flask backend server
flask run --host=0.0.0.0 --port=5000
```

### 3. Frontend Setup
```bash
# In a separate terminal:
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Running Tests
```bash
# Run backend pytest suite (245 tests)
cd backend
python -m pytest tests/ -v

# Run backend property-based tests with Hypothesis statistics
python -m pytest tests/test_ml_service_properties.py -v --hypothesis-show-statistics

# Run frontend test suite
cd frontend
npm run test:run
```

---

## 🌐 Deployment Status & Hosting Architecture

DeceptiScan is designed to be hosted with the React frontend on **Vercel** and the Flask/PyTorch backend on a persistent container host (**Render** / **Railway**).

> **Deployment Note**: The production backend is not currently running on a public live instance to maintain a zero-cost profile. Real-time memory profiling shows that the loaded PyTorch runtime, DistilBERT classification weights, and Sentence-Transformers retrieval model require **~693.84 MB peak RSS**, exceeding standard 512MB free-tier limits (such as Render Free). Lighter production pathways (such as INT8/ONNX model quantization, separate serverless worker pools, or the Hugging Face Inference API) are scoped for future cost-free hosting.

---

## ⚠️ Known Limitations & Engineering Tradeoffs

Documenting what is intentionally out-of-scope or planned for future iterations:

1. **In-Memory ML Footprint**: Loading DistilBERT and Sentence-Transformers concurrently inside the Flask web process requires ~694 MB of resident RAM. In a high-scale production setup, inference would be offloaded to asynchronous task workers (Celery/Redis Queue) or an external inference endpoint with WebSocket status streaming.
2. **Stage 1 Retrieval Circularity**: The current ~8,200 claim retrieval corpus is populated from the LIAR *training* split. This validates the end-to-end pgvector embedding pipeline, but retrieved statements reflect the classifier's training distribution rather than independent external fact-checks. Stage 2 routing via the Google Fact Check Tools API is scaffolded in `recency_service.py` to close this loop.
3. **Google OAuth & Social Login**: Authentication currently supports email/password with bcrypt hashing and JWT tokens; Google OAuth2 and third-party provider flows are explicitly scoped as planned future extensions.
4. **Theme Customization & System Settings**: The Investigator Profile UI displays aesthetic placeholders for terminal theme toggles and system preference panels; full theme-switching state persistence is planned for a subsequent UI iteration.
5. **Rate Limiting Middleware**: Rate limiting logic exists in `services/cache.py` (`check_rate_limit`) with fail-open semantics, but is not currently attached as active middleware to `/api/v1/analyze`.
6. **Test Database Isolation**: The pytest suite connects to the configured `DATABASE_URL` rather than an isolated ephemeral test database, relying on explicit `DELETE` loops during fixture teardown.

---

## 📸 Screenshots & UI Preview

> *To update screenshots, place your image or GIF in the `docs/assets/` directory with the matching filenames below.*

### 1. Investigator Dossier & Live Authenticity Meter
*Desktop view showing full text submission, sentence-by-sentence reliability flags, and authenticity gauge.*

```
+-----------------------------------------------------------------------+
|  [Bureau Case File: #DAE770B5]                  [Authenticity: 62/100]|
|  Classification: MIXED                                                |
|                                                                       |
|  [Sentence 1] "The economic growth rate exceeded all projections..."  |
|               -> Flag: Loaded Language | Score: 42% (Unreliable)      |
|                                                                       |
|  [Sentence 2] "According to department figures released Tuesday..."   |
|               -> Flag: Factual Citation | Score: 88% (Reliable)       |
+-----------------------------------------------------------------------+
```
*(Drop screenshot at `docs/assets/analysis_dashboard.png`)*

### 2. Semantic Claim Grounding (pgvector Search)
*Evidence modal displaying semantically similar verified statements retrieved via cosine distance.*

*(Drop screenshot/GIF at `docs/assets/retrieval_modal.gif`)*

---

## 📄 License

This project is proprietary — see [LICENSE](LICENSE) for details.
