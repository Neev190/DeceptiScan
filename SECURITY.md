# Security Notes

This document records explicit security decisions and tradeoffs in the DeceptiScan codebase. The intent is to make implicit choices visible so they can be revisited deliberately rather than discovered by accident.

---

## Rate Limiting

### Current state

Rate limiting is implemented in `backend/services/cache.py` (`check_rate_limit`) but is **not currently wired to the `/api/v1/analyze` endpoint**. It is present in the codebase as infrastructure but not enforced on the primary analysis route.

Planned limits (not yet active — these are specified in the design but not currently enforced on any route):
- Anonymous: 10 requests/minute
- Authenticated: 60 requests/minute

### Fail-open on Redis unavailability

**Decision: rate limiting fails open.**

When Redis is unreachable, `check_rate_limit` catches `redis.RedisError` and returns `(True, limit)` — the request is allowed through unconditionally. This means a Redis outage grants unlimited throughput to all clients for the duration of the outage.

**Rationale for fail-open:** A Redis outage should not take down the API. Failing closed (rejecting all requests when the rate-limit counter is unreadable) would make Redis a hard availability dependency for a feature that is itself a protective measure. For a public analysis tool, availability is prioritised over rate-limit enforcement during infrastructure failures.

**Residual risk:** During a Redis outage, the ML inference pipeline is exposed to unbounded request volume. A sustained outage combined with a traffic spike could exhaust CPU/memory. Mitigation options if this becomes a concern: a short-TTL in-process counter as a secondary floor, or an infrastructure-level rate limit at the reverse proxy (nginx).

**Owner decision required when:** rate limiting is wired to `/analyze`. The fail-open tradeoff should be re-evaluated at that point with concrete traffic expectations in mind.

---

## Analysis Result Caching

### Read miss on Redis unavailability

`get_analysis` catches `redis.RedisError` and returns `None`. The request proceeds to full ML inference. No exception propagates to the caller.

**Effect:** Redis outage = 100% cache miss rate. Every request hits the ML pipeline. Latency increases; correctness is unaffected.

### Write failure on Redis unavailability

`set_analysis` catches `redis.RedisError` and returns `False`. The return value is not checked in `analysis.py`. The response is still returned to the client.

**Effect:** Results computed during a Redis outage are never cached. When Redis recovers, the cache starts cold for any content analyzed during the outage window. No data is lost; the cache simply does not warm.

**Monitoring note:** Redis write/read failures are only logged via `print()` to stdout. In production these should route to a structured logger so cache-miss spikes are distinguishable from inference latency spikes in dashboards.

---

## Prompt Injection Mitigation

Retrieved claims from the LIAR corpus are sanitized before being included in any downstream ML context. `_sanitize_claim_text` in `analysis.py` strips common injection patterns (`ignore`, `disregard`, `system:`, role delimiters, etc.) and caps claim text at 300 characters.

**Limitation:** The sanitizer uses a static regex list. Novel injection patterns not in the list pass through. The primary defence is that the current model (DistilBERT classifier) does not execute instructions — it produces a probability distribution over labels. The injection surface exists only if the architecture changes to include a generative or instruction-following component.

---

## JWT Token Storage

Access tokens expire in 1 hour; refresh tokens in 24 hours (configurable via environment variables `JWT_ACCESS_TOKEN_EXPIRES`, `JWT_REFRESH_TOKEN_EXPIRES`). Token revocation is not currently implemented — a stolen token is valid until expiry. This is an accepted tradeoff for the current scope; a revocation blocklist (Redis-backed) should be added before production deployment.

---

## Secrets Management

### Credential exposure incidents

**Incident 1 and 2:** A live Neon DB connection string (including plaintext password) was pasted directly into chat during debugging sessions on two separate occasions. Both incidents were identified promptly, the credentials were rotated immediately after each exposure, and the old credentials were confirmed dead (connection attempts with the old values fail). No evidence of third-party access during either window.

This is documented plainly here rather than glossed over. The appropriate response for any future credential exposure of this kind is the same: rotate first, confirm the old value is rejected, then document.

**Current state of `.env`:** The `.env` file contains live credentials for the Neon DB and Upstash Redis instances. It is `.gitignore`d and must not be committed. `.env.example` contains only placeholder values and is safe to commit.

---

## Input Validation

All `/analyze` requests are validated via `validate_analyze_request` before reaching the ML pipeline. `MAX_CONTENT_LENGTH` is enforced at the Flask layer (default 50,000 bytes). Source URLs are validated for format but not fetched server-side, so SSRF is not a concern on the current architecture.
