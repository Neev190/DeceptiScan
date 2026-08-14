# Testing Documentation

## Test Suite Overview

**Current Status**: 245 tests passing (clean baseline)

The test suite covers authentication, JWT edge cases, ML service functionality, retrieval operations, input validation, security vulnerabilities, bug regression prevention, and full end-to-end integration flows.

### Test Breakdown by File

- **test_validators.py**: 45 tests — Input validation for content, URLs, titles, authentication requests, and feedback
- **test_ml_service.py**: 43 tests — ML model loading, inference, text preprocessing, sentence analysis, classification thresholds
- **test_jwt_auth_edge_cases.py**: 31 tests — Malformed/expired token handling across protected and optional-auth routes
- **test_auth.py**: 29 tests — Registration, login, logout, token refresh, password validation, user profile operations
- **test_stored_xss.py**: 24 tests — XSS payload handling in content, title, and username fields (parametrized)
- **test_bug_regressions.py**: 15 tests — Password length limits, non-UUID analysis IDs, username type safety
- **test_ml_service_properties.py**: 12 tests — Property-based testing for ML service boundaries and invariants
- **test_retrieve_endpoint.py**: 12 tests — Similar claims retrieval, error handling, sanitization
- **test_retrieval_service.py**: 11 tests — Retrieval service loading, similarity search, threshold filtering
- **test_api_validation.py**: 10 tests — API endpoint validation errors, content length limits, field requirements
- **test_analysis_endpoints.py**: 6 tests — Analysis creation, retrieval, history, authenticated operations
- **test_jwt_optional_auth_regression.py**: 6 tests — JWT consistency across optional-auth endpoints
- **test_full_integration.py**: 1 test — Complete end-to-end workflow from registration through analysis deletion

## JWT Edge-Case Testing

### The /feedback Optional-Auth Bug

**Root Cause**: The `/feedback` endpoint used `@jwt_required(optional=True)` but didn't degrade gracefully on malformed or expired tokens the way `/analyze` did. Malformed tokens caused 422 Unprocessable Entity errors instead of treating the request as anonymous.

**Fix Applied**: Wrapped `verify_jwt_in_request(optional=True)` in try/except blocks to catch JWT decode errors and proceed as anonymous requests, matching `/analyze` behavior.

**Test Coverage Added**: 14 tests specifically covering the optional-auth degradation bug across `TestOptionalAuthRoutes`, `TestOptionalAuthConsistency` (test_jwt_auth_edge_cases.py) and `TestJWTOptionalAuthRegression` (test_jwt_optional_auth_regression.py):
- Malformed tokens (invalid base64, corrupted signatures, non-JWT strings)
- Expired tokens (both access and refresh tokens)
- Missing Authorization headers and malformed Bearer formats
- Consistency verification across all optional-auth routes
- Edge cases like empty Bearer tokens and multiple Authorization headers

## Stored XSS Testing

### Methodology and Findings

**Test Strategy**: Submit XSS payloads (`<script>alert(1)</script>`, `<img src=x onerror=alert(1)>`, `"><svg onload=alert(1)>`) through all user-input fields and verify:
1. No 500 errors (application doesn't crash)
2. Payloads are returned as inert plain text (not interpreted as markup)

**Key Finding**: HTML tags are stripped by the ML service's text preprocessor, neutralizing XSS execution risk at the data layer.

**Additional Fix**: Corrected inconsistent JSON response keys (`token` vs `access_token`) that were causing frontend parsing issues.

## Load Testing

Load testing has not yet been run against this build. A load test script exists at `backend/load_test.py` which can simulate concurrent users hitting the `/api/v1/analyze` endpoint and provides p50/p95/p99 latency metrics, but no test execution results are currently available.

## Adversarial/Bias Sensitivity Testing

### Control Group Design

**Methodology**: Systematic sensitivity analysis using matched content pairs to measure model consistency under input variations.

### Results

- **Mean Score Delta**: -2.48 points
- **Maximum Absolute Delta**: 3.7 points  
- **Threshold Compliance**: Both values well under the 15-point stability threshold
- **Model Determinism**: Control group standard deviation = 0.0 (fully deterministic)

**Important**: Results are framed as **sensitivity analysis**, not bias testing. No causal claims are made about fairness or discrimination — this measures technical consistency only.

## Test Suite Infrastructure

### Known Limitations

#### No Test/Production Database Isolation

**Critical Finding**: Tests connect directly to the real Neon production database. Confirmed via runtime inspection of `db.engine.url` and live `SELECT current_database()` query.

- No separate `TEST_DATABASE_URL` is configured
- Teardown performs real `DELETE FROM` statements (not `drop_all()`, not transaction rollback) against every table except `claim_embeddings`
- Changes are committed to live Neon infrastructure
- Test data does not currently accumulate (verified via direct row-count checks returning 0)
- **Recommendation**: Establish separate test database before using this suite with real user data

#### Shared Session Fragility (Resolved)

**Issue Found and Fixed**: Flask-SQLAlchemy's `db.session` is a global `scoped_session` shared across all test files in the same pytest process, even though each file's `create_app('testing')` call creates its own `db.engine`. 

**Proof Method**: Overlapping app-context `is` comparison confirmed identical session objects, then verified via matching session IDs in live pytest runs.

**Impact**: An unguarded `db.session.commit()` in test teardown could leave the shared session in Postgres's aborted-transaction state, causing unrelated `ForeignKeyViolation` failures in subsequent tests.

**Resolution**: Every fixture's teardown now wraps the DELETE-loop + commit in try/except with `rollback()` on failure, plus defensive `rollback()` at setup. This resolved 2 test failures that briefly broke the 245/245 baseline.

#### JWT Test Key Configuration

**Historical Issue**: `test_auth.py` previously hardcoded a 19-byte JWT signing key, triggering security warnings.

**Current Status**: Updated to 32+ byte key. The app's fallback default in `app/__init__.py` remains at 17 bytes (`'dev-jwt-secret-key'`) but no `InsecureKeyLengthWarning` fires during test execution.

## Known Gaps

**JWT Fallback Default**: The application's JWT fallback default in `create_app()` config (`'dev-jwt-secret-key'`, 17 bytes) is still short in the code, but it never actually triggers in practice because the `.env` file's real `JWT_SECRET_KEY` (32+ bytes) is always loaded first. Confirmed directly by printing `app.config['JWT_SECRET_KEY']` at runtime: the 32+ byte production key is used, not the fallback default.

## Test Execution

```bash
# Run full suite
cd backend && python -m pytest tests/ -v

# Run with property-based testing statistics
cd backend && python -m pytest tests/ -v --hypothesis-show-statistics

# Run specific test categories
cd backend && python -m pytest tests/test_jwt_auth_edge_cases.py -v
cd backend && python -m pytest tests/test_ml_service_properties.py -v
```

All tests pass consistently against the current codebase. The suite provides comprehensive coverage of security edge cases, input validation, model behavior, and integration scenarios.