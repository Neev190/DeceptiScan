---
name: testing
description: Write and run tests for both backend (pytest, Hypothesis) and frontend (Vitest, Testing Library).
---

## Testing — DeceptiScan

### Backend Tests (pytest)

**Tech:** pytest, Hypothesis (property-based), pytest-cov

**Run all backend tests:**
```bash
cd backend && python -m pytest tests/ -v
```

**Run with coverage:**
```bash
cd backend && python -m pytest tests/ --cov=app --cov=models --cov=services -v
```

**Run property-based tests:**
```bash
cd backend && python -m pytest tests/ -v --hypothesis-show-statistics
```

**Existing test files:**

| File | Tests |
|---|---|
| `tests/test_validators.py` | Input validation (content length, URL, email format) |
| `tests/test_api_validation.py` | API endpoint validation |
| `tests/test_auth.py` | Register, login, me, refresh, logout flows |
| `tests/test_ml_service.py` | ML service analyze, preprocessing, classification |
| `tests/test_ml_service_properties.py` | Hypothesis property tests |

**Coverage targets:**
- Backend: 80%+ overall
- ML Service utilities: 85%+

### Frontend Tests (Vitest + Testing Library)

**Tech:** Vitest, @testing-library/react, @testing-library/jest-dom, jsdom

**Run all frontend tests:**
```bash
cd frontend && npm test
```

**Run in watch mode:**
```bash
cd frontend && npm test --
```

**Existing test files:**
- `src/components/ArticleInput.test.tsx` — rendering, validation, submission
- `src/components/ScoreMeter.test.tsx` — score display, colors, labels
- `src/components/integration.test.tsx` — end-to-end user workflow

**Coverage targets:** 70%+ component coverage

### Property-Based Testing (Hypothesis)

10 correctness properties from `design.md`:

| # | Property | Validates |
|---|---|---|
| 1 | 0 ≤ authenticityScore ≤ 100 | Requirements 1, 3 |
| 2 | Classification matches score thresholds | Requirements 3.4–3.6 |
| 3 | All sentences appear in results | Requirement 1.4 |
| 4 | Score meter green/red color consistency | Requirement 1.4 |
| 5 | Low confidence → unknown + warning | Requirement 4 |
| 6 | Repeat submission returns cached result | Requirement 11 |
| 7 | Response completeness (all required fields) | Requirement 3 |
| 8 | Empty/oversized input → INVALID_INPUT | Requirement 2 |
| 9 | Feedback stored with valid IDs | Requirement 8 |
| 10 | Rate limit enforcement (10/60 per min) | Requirement 9 |

### Writing Tests

**Backend test pattern:**
```python
def test_endpoint(client, auth_headers):
    response = client.post('/api/v1/analyze', json={...}, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 0 <= data['authenticityScore'] <= 100
```

**Frontend test pattern:**
```typescript
import { render, screen } from '@testing-library/react';
import { Component } from './Component';

test('renders with correct score', () => {
  render(<Component score={85} label="Reliable" />);
  expect(screen.getByText(/85/)).toBeInTheDocument();
});
```
